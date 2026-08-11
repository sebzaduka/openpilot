import unittest
from types import SimpleNamespace

from opendbc.car.rivian.ext_controller import ExternalController, HANDS_OFF_EXIT_FRAMES, MIN_TORQUE_EXIT_SPEED, MIN_TORQUE_FRAMES
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.fingerprints import FW_VERSIONS
from opendbc.car.rivian.values import CAR, FW_QUERY_CONFIG, WMI, ModelLine, ModelYear
from opendbc.car import structs
from opendbc.sunnypilot.car.rivian.values import RivianFlagsSP, RivianSafetyFlagsSP


def _fake_controller_state(*, standstill: bool, v_ego_raw: float):
  return SimpleNamespace(
    out=SimpleNamespace(
      standstill=standstill,
      vEgoRaw=v_ego_raw,
      steeringPressed=False,
      steeringAngleDeg=0.0,
      steeringRateDeg=0.0,
      steeringTorque=0.0,
    ),
    eac_status=1,
    eac_error_code=0,
    hands_on_level=0,
    sccm_wheel_touch={
      "SCCM_WheelTouch_Calibration": 100.0,
      "SCCM_WheelTouch_CapacitiveValue": 0.0,
    },
  )


def _update_torque_handoff(erc: ExternalController, *, standstill: bool, v_ego_raw: float) -> None:
  CS = _fake_controller_state(standstill=standstill, v_ego_raw=v_ego_raw)
  erc._update_hands_on(CS)
  erc.hands_off_frames = HANDS_OFF_EXIT_FRAMES
  erc._update_torque_active(CS, lat_active=True, desired_angle=0.0)


def _update_fresh_engagement(erc: ExternalController, *, standstill: bool, v_ego_raw: float) -> None:
  CS = _fake_controller_state(standstill=standstill, v_ego_raw=v_ego_raw)
  erc._update_hands_on(CS)
  erc._update_torque_active(CS, lat_active=True, desired_angle=0.0)


class TestRivian(unittest.TestCase):
  def test_longitudinal_harness_sets_matching_runtime_and_safety_flags(self):
    CP = structs.CarParams()
    CP_SP = structs.CarParamsSP()

    CarInterface._get_params_sp(CP, CP_SP, CAR.RIVIAN_R1, {1: {0x131A: 7}}, [], False, False, False)

    self.assertTrue(CP_SP.flags & RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE)
    self.assertTrue(CP_SP.safetyParam & RivianSafetyFlagsSP.LONGITUDINAL_HARNESS_UPGRADE)

  def test_custom_fuzzy_fingerprinting(self):
    for platform in CAR:
      with self.subTest(platform=platform.name):
        for wmi in WMI:
          for line in ModelLine:
            for year in ModelYear:
              for bad in (True, False):
                vin = ["0"] * 17
                vin[:3] = wmi
                vin[3] = line.value
                vin[9] = year.value
                if bad:
                  vin[3] = "Z"
                vin = "".join(vin)

                matches = FW_QUERY_CONFIG.match_fw_to_car_fuzzy({}, vin, FW_VERSIONS)
                should_match = year in platform.config.years and not bad
                assert (matches == {platform}) == should_match, "Bad match"

  def test_cooperative_torque_handoff_stays_active_at_standstill(self):
    CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
    erc = ExternalController(CP)
    erc.torque_active = True
    erc.torque_active_frames = MIN_TORQUE_FRAMES

    _update_torque_handoff(erc, standstill=True, v_ego_raw=0.0)

    self.assertTrue(erc.torque_active)

  def test_fresh_engagement_uses_torque_at_standstill(self):
    CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
    erc = ExternalController(CP)

    _update_fresh_engagement(erc, standstill=True, v_ego_raw=0.0)

    self.assertTrue(erc.torque_active)

  def test_fresh_engagement_uses_torque_below_min_speed(self):
    CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
    erc = ExternalController(CP)

    _update_fresh_engagement(erc, standstill=False, v_ego_raw=MIN_TORQUE_EXIT_SPEED - 0.1)

    self.assertTrue(erc.torque_active)

  def test_fresh_engagement_uses_angle_above_min_speed(self):
    CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
    erc = ExternalController(CP)

    _update_fresh_engagement(erc, standstill=False, v_ego_raw=MIN_TORQUE_EXIT_SPEED + 0.1)

    self.assertFalse(erc.torque_active)

  def test_cooperative_torque_handoff_stays_active_below_min_speed(self):
    CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
    erc = ExternalController(CP)
    erc.torque_active = True
    erc.torque_active_frames = MIN_TORQUE_FRAMES

    _update_torque_handoff(erc, standstill=False, v_ego_raw=MIN_TORQUE_EXIT_SPEED - 0.1)

    self.assertTrue(erc.torque_active)

  def test_cooperative_torque_handoff_clears_above_min_speed(self):
    CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
    erc = ExternalController(CP)
    erc.torque_active = True
    erc.torque_active_frames = MIN_TORQUE_FRAMES

    _update_torque_handoff(erc, standstill=False, v_ego_raw=MIN_TORQUE_EXIT_SPEED + 0.1)

    self.assertFalse(erc.torque_active)
