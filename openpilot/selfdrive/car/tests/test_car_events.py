from openpilot.cereal import log
from opendbc.car import structs
from opendbc.car.rivian.values import CAR

from openpilot.selfdrive.car.car_events import CarEvents


EventName = log.OnroadEvent.EventName
GearShifter = structs.CarState.GearShifter


def get_rivian_park_events():
  CP = structs.CarParams(brand="rivian", carFingerprint=CAR.RIVIAN_R1)
  CS = structs.CarState(gearShifter=GearShifter.park)
  CS.cruiseState.available = True
  CS.cruiseState.enabled = True

  return CarEvents(CP).update(CS, structs.CarState(), structs.CarControl())


def test_rivian_park_immediately_disables_longitudinal():
  events = get_rivian_park_events()

  assert events.has(EventName.pcmDisable)
  assert events.has(EventName.wrongGear)
