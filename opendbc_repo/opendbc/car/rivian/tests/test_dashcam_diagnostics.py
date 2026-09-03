from opendbc.car.rivian.interface import CarInterface


def test_angle_upgrade_present():
  assert CarInterface._dashcam_reason({1: {0x1310: 8}}) is None


def test_angle_upgrade_missing():
  assert CarInterface._dashcam_reason({1: {0x131A: 8}}) == "RIVIAN_ANGLE_UPGRADE_NOT_DETECTED"


def test_angle_upgrade_bus_missing():
  assert CarInterface._dashcam_reason({0: {0x321: 8}}) == "RIVIAN_ANGLE_UPGRADE_NOT_DETECTED"
