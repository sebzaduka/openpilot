"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import math
from enum import StrEnum

from opendbc.car import Bus, DT_CTRL, structs
from opendbc.can.parser import CANParser
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian.values import DBC
from opendbc.sunnypilot.car.rivian.values import RivianFlagsSP

ButtonType = structs.CarState.ButtonEvent.Type

MAX_SET_SPEED = 85 * CV.MPH_TO_MS
MIN_SET_SPEED = 20 * CV.MPH_TO_MS
RIGHT_SCROLL_CLICK_VALUE = 2
RIGHT_SCROLL_LONG_PRESS_FRAMES = int(1.0 / DT_CTRL)


class CarStateExt:
  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP):
    self.CP = CP
    self.CP_SP = CP_SP

    self.set_speed = 10
    self.increase_button = False
    self.decrease_button = False
    self.distance_button = 0
    self.increase_counter = 0
    self.decrease_counter = 0
    self.acm_accel_last = 0.0
    self.acm_rail_counter = 0
    self.right_scroll_press_frames = 0
    self.right_scroll_long_press_triggered = False
    self.right_scroll_blocked_until_release = False

  def _update_right_scroll_long_press(self, pressed: bool, trailer_status: int | None) -> bool:
    """Return True once when a continuous press reaches the long-press threshold."""
    if not pressed:
      self.right_scroll_press_frames = 0
      self.right_scroll_long_press_triggered = False
      self.right_scroll_blocked_until_release = False
      return False

    if trailer_status is not None and trailer_status != 0:
      self.right_scroll_press_frames = 0
      self.right_scroll_long_press_triggered = False
      self.right_scroll_blocked_until_release = True
      return False

    if self.right_scroll_blocked_until_release:
      return False

    if trailer_status is None:
      self.right_scroll_press_frames = 0
      self.right_scroll_long_press_triggered = False
      return False

    self.right_scroll_press_frames += 1
    if not self.right_scroll_long_press_triggered and self.right_scroll_press_frames >= RIGHT_SCROLL_LONG_PRESS_FRAMES:
      self.right_scroll_long_press_triggered = True
      return True

    return False

  def update_longitudinal_upgrade(self, ret: structs.CarState, can_parsers: dict[StrEnum, CANParser]) -> None:
    cp_park = can_parsers[Bus.alt]
    cp_adas = can_parsers[Bus.adas]
    cp = can_parsers[Bus.pt]

    prev_increase_button = self.increase_button
    prev_decrease_button = self.decrease_button

    right_scroll_pressed = cp_park.vl["WheelButtons_Fwd"]["RightButton_ScrollClick"] == RIGHT_SCROLL_CLICK_VALUE
    trailer_status = int(cp.vl["VDM_CGM_GW"]["CGM_TrailerPresent"])
    trailer_status_seen = cp.ts_nanos["VDM_CGM_GW"]["CGM_TrailerPresent"] != 0
    trailer_status = trailer_status if trailer_status_seen else None
    if self._update_right_scroll_long_press(right_scroll_pressed, trailer_status):
      ret.buttonEvents = [*ret.buttonEvents, structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

    if self.CP.openpilotLongitudinalControl:
      cp_cam = can_parsers[Bus.cam]

      # distance scroll wheel
      right_scroll = cp_park.vl["WheelButtons_Fwd"]["RightButton_Scroll"]
      if right_scroll != 255:
        if self.distance_button != right_scroll:
          ret.buttonEvents = [*ret.buttonEvents, structs.CarState.ButtonEvent(pressed=False, type=ButtonType.gapAdjustCruise)]
        self.distance_button = right_scroll

      # button logic for set-speed
      self.increase_button = cp_park.vl["WheelButtons_Fwd"]["RightButton_RightClick"] == 2
      self.decrease_button = cp_park.vl["WheelButtons_Fwd"]["RightButton_LeftClick"] == 2

      self.increase_counter = self.increase_counter + 1 if self.increase_button else 0
      self.decrease_counter = self.decrease_counter + 1 if self.decrease_button else 0

      metric = cp_adas.vl["Cluster"]["Cluster_Unit"] == 0
      conversion = CV.KPH_TO_MS if metric else CV.MPH_TO_MS
      long_press_step = 10.0 if metric else 5.0
      set_speed_converted = self.set_speed * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)

      if self.increase_button:
        if self.increase_counter % 66 == 0:
          self.set_speed = (int(math.ceil((set_speed_converted + 1) / long_press_step)) * long_press_step) * conversion
        elif not prev_increase_button:
          self.set_speed += conversion

      if self.decrease_button:
        if self.decrease_counter % 66 == 0:
          self.set_speed = (int(math.floor((set_speed_converted - 1) / long_press_step)) * long_press_step) * conversion
        elif not prev_decrease_button:
          self.set_speed -= conversion

      if not ret.cruiseState.enabled:
        self.set_speed = ret.vEgoCluster

      # VDM_UserAdasRequest: 0=IDLE, 1=UP_1, 2=UP_2, 3=DOWN_1, 4=DOWN_2
      stalk_down = int(cp.vl["VDM_AdasSts"]["VDM_UserAdasRequest"]) in (3, 4)
      if stalk_down:
        # Mimic Rivian ACC: stalk down sets speed to current speed (never decreases)
        self.set_speed = max(self.set_speed, ret.vEgoCluster)

      # stock ACM stuck at its decel rail: our set speed sits above the ACM's target
      acm_accel = cp_cam.vl["ACM_longitudinalRequest"]["ACM_AccelerationRequest"]
      settled = abs(ret.vEgo - self.set_speed) < 0.5 * conversion
      stuck = ret.cruiseState.enabled and settled and acm_accel == -3.92 and acm_accel == self.acm_accel_last
      self.acm_accel_last = acm_accel
      self.acm_rail_counter = self.acm_rail_counter + 1 if stuck else 0

      if self.acm_rail_counter >= 1000:
        self.set_speed -= conversion
        self.acm_rail_counter = 0

      self.set_speed = max(MIN_SET_SPEED, min(self.set_speed, MAX_SET_SPEED))
      ret.cruiseState.speed = self.set_speed

    if self.CP.enableBsm:
      ret.leftBlindspot = cp_park.vl["BSM_BlindSpotIndicator_Fwd"]["BSM_BlindSpotIndicator_Left"] != 0
      ret.rightBlindspot = cp_park.vl["BSM_BlindSpotIndicator_Fwd"]["BSM_BlindSpotIndicator_Right"] != 0

  def update(self, ret: structs.CarState, can_parsers: dict[StrEnum, CANParser]) -> None:
    if self.CP_SP.flags & RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE:
      self.update_longitudinal_upgrade(ret, can_parsers)

  @staticmethod
  def get_parser(CP, CP_SP) -> dict[StrEnum, CANParser]:
    messages = {}

    if CP_SP.flags & RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE:
      messages[Bus.alt] = CANParser(DBC[CP.carFingerprint][Bus.alt], [], 1)

    return messages
