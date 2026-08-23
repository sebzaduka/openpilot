from opendbc.car import get_safety_config, structs
from opendbc.car.carlog import carlog
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.rivian.carcontroller import CarController
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.radar_interface import RadarInterface
from opendbc.car.rivian.values import RivianFlags, RivianSafetyFlags
from opendbc.sunnypilot.car.rivian.values import RivianFlagsSP, RivianSafetyFlagsSP


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController
  RadarInterface = RadarInterface

  @staticmethod
  def _dashcam_reason(fingerprint: dict[int, dict[int, int]]) -> str | None:
    return None if 0x1310 in fingerprint.get(1, {}) else "RIVIAN_ANGLE_UPGRADE_NOT_DETECTED"

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = "rivian"

    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.rivian)]

    # GEN2 (2025+) doesn't have SCCM_WheelTouch on the bus
    if 0x321 not in fingerprint[0]:
      ret.flags |= RivianFlags.GEN2.value

    # no angle upgrade installed
    dashcam_reason = CarInterface._dashcam_reason(fingerprint)
    if dashcam_reason is not None:
      ret.dashcamOnly = True

    carlog.error({
      "event": "rivian_startup_diagnostic",
      "candidate": str(candidate),
      "dashcam_only": ret.dashcamOnly,
      "dashcam_reason": dashcam_reason or "NONE",
      "angle_upgrade_0x1310_bus1": 0x1310 in fingerprint.get(1, {}),
      "longitudinal_upgrade_0x131a_bus1": 0x131a in fingerprint.get(1, {}),
      "bus_address_counts": {str(bus): len(addresses) for bus, addresses in fingerprint.items()},
    })

    ret.steerActuatorDelay = 0.1
    ret.steerAtStandstill = True
    ret.steerLimitTimer = 0.4
    CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)

    # torque is the primary channel, ext_controller derives the angle from curvature
    ret.steerControlType = structs.CarParams.SteerControlType.torque
    ret.radarUnavailable = True

    # TODO: pending finding/handling missing set speed
    ret.alphaLongitudinalAvailable = False
    if alpha_long:
      ret.openpilotLongitudinalControl = True
      ret.safetyConfigs[0].safetyParam |= RivianSafetyFlags.LONG_CONTROL.value

    ret.longitudinalActuatorDelay = 0.25
    ret.stopAccel = -0.2
    ret.longitudinalTuning.kiBP = [0.]
    ret.longitudinalTuning.kiV = [0.2]

    return ret

  @staticmethod
  def _get_params_sp(stock_cp: structs.CarParams, ret: structs.CarParamsSP, candidate, fingerprint: dict[int, dict[int, int]],
                     car_fw: list[structs.CarParams.CarFw], alpha_long: bool, is_release_sp: bool, docs: bool) -> structs.CarParamsSP:
    if 0x131a in fingerprint[1]:
      ret.flags |= RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE.value
      ret.safetyParam |= RivianSafetyFlagsSP.LONGITUDINAL_HARNESS_UPGRADE
      stock_cp.radarUnavailable = False
      stock_cp.enableBsm = True
      stock_cp.alphaLongitudinalAvailable = True

    if alpha_long and stock_cp.alphaLongitudinalAvailable:
      stock_cp.openpilotLongitudinalControl = True
      stock_cp.safetyConfigs[0].safetyParam |= RivianSafetyFlags.LONG_CONTROL.value

    return ret
