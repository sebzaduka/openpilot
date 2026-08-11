from types import SimpleNamespace

from opendbc.can.parser import CANParser
from opendbc.car import Bus, structs
from opendbc.sunnypilot.car.rivian.carstate_ext import (
  RIGHT_SCROLL_LONG_PRESS_FRAMES,
  CarStateExt,
)


def build_detector() -> CarStateExt:
  CP = SimpleNamespace(openpilotLongitudinalControl=False, enableBsm=False)
  return CarStateExt(CP, SimpleNamespace())


def hold(detector: CarStateExt, press_frames: int, trailer_status: int | None = 0) -> bool:
  triggered = False
  for _ in range(press_frames):
    triggered |= detector._update_right_scroll_long_press(True, trailer_status)
  return triggered


def update_with_trailer_status(detector: CarStateExt, pressed: bool, trailer_status: int, status_seen: bool) -> bool:
  ret = structs.CarState()
  cp = SimpleNamespace(
    vl={"VDM_CGM_GW": {"CGM_TrailerPresent": trailer_status}},
    ts_nanos={"VDM_CGM_GW": {"CGM_TrailerPresent": int(status_seen)}},
  )
  cp_park = SimpleNamespace(vl={"WheelButtons_Fwd": {"RightButton_ScrollClick": 2 if pressed else 0}})
  detector.update_longitudinal_upgrade(ret, {Bus.pt: cp, Bus.adas: SimpleNamespace(), Bus.alt: cp_park})
  return any(be.type == structs.CarState.ButtonEvent.Type.lkas and be.pressed for be in ret.buttonEvents)


def test_right_scroll_short_press_does_not_trigger():
  detector = build_detector()

  assert not hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES - 1)
  assert not detector._update_right_scroll_long_press(False, 0)


def test_right_scroll_long_press_triggers_at_threshold():
  detector = build_detector()

  assert not hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES - 1)
  assert detector._update_right_scroll_long_press(True, 0)


def test_right_scroll_continuous_hold_triggers_only_once():
  detector = build_detector()

  assert hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES)
  for _ in range(RIGHT_SCROLL_LONG_PRESS_FRAMES):
    assert not detector._update_right_scroll_long_press(True, 0)


def test_right_scroll_release_allows_another_long_press():
  detector = build_detector()

  assert hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES)
  assert not detector._update_right_scroll_long_press(False, 0)
  assert hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES)


def test_right_scroll_separate_short_presses_do_not_accumulate():
  detector = build_detector()

  for _ in range(3):
    assert not hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES // 2)
    assert not detector._update_right_scroll_long_press(False, 0)


def test_right_scroll_long_press_blocked_with_trailer():
  detector = build_detector()

  assert not hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES, trailer_status=1)


def test_right_scroll_trailer_connected_during_hold_requires_release():
  detector = build_detector()

  assert not hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES // 2)
  assert not detector._update_right_scroll_long_press(True, 1)
  assert not hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES, trailer_status=0)

  assert not detector._update_right_scroll_long_press(False, 0)
  assert hold(detector, RIGHT_SCROLL_LONG_PRESS_FRAMES)


def test_trailer_status_lazy_parser_initialization():
  detector = build_detector()
  ret = structs.CarState()
  cp = CANParser("rivian_primary_actuator", [], 0)
  cp_park = SimpleNamespace(vl={"WheelButtons_Fwd": {"RightButton_ScrollClick": 0}})

  detector.update_longitudinal_upgrade(ret, {Bus.pt: cp, Bus.adas: SimpleNamespace(), Bus.alt: cp_park})

  assert cp.ts_nanos["VDM_CGM_GW"]["CGM_TrailerPresent"] == 0
  assert not ret.buttonEvents


def test_right_scroll_event_blocked_with_unsafe_trailer_status():
  for trailer_status in (1, 2, 3):
    detector = build_detector()
    triggered = False
    for _ in range(RIGHT_SCROLL_LONG_PRESS_FRAMES):
      triggered |= update_with_trailer_status(detector, True, trailer_status, True)
    assert not triggered


def test_right_scroll_unseen_then_absent_starts_hold_timing():
  detector = build_detector()
  triggered = False
  for _ in range(RIGHT_SCROLL_LONG_PRESS_FRAMES // 2):
    triggered |= update_with_trailer_status(detector, True, 0, False)
  assert not triggered

  for _ in range(RIGHT_SCROLL_LONG_PRESS_FRAMES - 1):
    triggered |= update_with_trailer_status(detector, True, 0, True)
  assert not triggered

  triggered |= update_with_trailer_status(detector, True, 0, True)
  assert triggered


def test_right_scroll_never_engages_without_trailer_status():
  detector = build_detector()
  triggered = False
  for _ in range(RIGHT_SCROLL_LONG_PRESS_FRAMES):
    triggered |= update_with_trailer_status(detector, True, 0, False)
  assert not triggered
