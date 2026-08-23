from openpilot.selfdrive.car.card import get_passive_reason


def test_passive_reasons():
  assert get_passive_reason(True, True, True) == "CARPARAMS_DASHCAM_ONLY"
  assert get_passive_reason(False, False, True) == "NO_CAR_CONTROLLER"
  assert get_passive_reason(False, True, False) == "OPENPILOT_ENABLED_TOGGLE_OFF"
  assert get_passive_reason(False, True, True) == "NONE"
