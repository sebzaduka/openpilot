from types import SimpleNamespace

from openpilot.cereal import custom, log
from opendbc.car import structs

from openpilot.selfdrive.selfdrived.events import Events
from openpilot.sunnypilot.mads.helpers import MadsSteeringModeOnBrake, set_car_specific_params
from openpilot.sunnypilot.mads.mads import ModularAssistiveDrivingSystem
from openpilot.sunnypilot.mads.state import StateMachine
from openpilot.sunnypilot.selfdrive.selfdrived.events import EventsSP
from opendbc.sunnypilot.car.rivian.values import RivianSafetyFlagsSP


State = custom.ModularAssistiveDrivingSystem.ModularAssistiveDrivingSystemState
EventName = log.OnroadEvent.EventName
EventNameSP = custom.OnroadEventSP.EventName
GearShifter = structs.CarState.GearShifter
ButtonType = structs.CarState.ButtonEvent.Type


class FakeParams:
  def put(self, *args, **kwargs):
    pass

  def put_bool(self, *args, **kwargs):
    pass

  def remove(self, *args, **kwargs):
    pass


def build_mads(gear: structs.CarState.GearShifter):
  events = Events()
  if gear != GearShifter.drive:
    events.add(EventName.wrongGear)
  if gear == GearShifter.reverse:
    events.add(EventName.reverseGear)

  selfdrive = SimpleNamespace(
    enabled=False,
    enabled_prev=False,
    CS_prev=structs.CarState(),
    events=events,
    events_sp=EventsSP(),
    state_machine=SimpleNamespace(current_alert_types=[], soft_disable_timer=0),
  )

  mads = ModularAssistiveDrivingSystem.__new__(ModularAssistiveDrivingSystem)
  mads.CP = structs.CarParams(brand="rivian")
  mads.selfdrive = selfdrive
  mads.events = selfdrive.events
  mads.events_sp = selfdrive.events_sp
  mads.enabled = True
  mads.active = True
  mads.allow_always = False
  mads.no_main_cruise = True
  mads.enabled_toggle = True
  mads.main_enabled_toggle = False
  mads.steering_mode_on_brake = MadsSteeringModeOnBrake.DISENGAGE
  mads.disengage_on_accelerator = True
  mads.lateral_mismatch_counter = 0
  mads.state_machine = StateMachine(mads)
  mads.state_machine.state = State.enabled

  CS = structs.CarState(gearShifter=gear, standstill=True)
  CS.cruiseState.available = True
  return mads, CS


def test_rivian_scroll_safety_flag_is_preserved():
  CP = structs.CarParams(brand="rivian")
  CP_SP = structs.CarParamsSP(safetyParam=RivianSafetyFlagsSP.LONGITUDINAL_HARNESS_UPGRADE)

  set_car_specific_params(CP, CP_SP, FakeParams())

  assert CP_SP.safetyParam & RivianSafetyFlagsSP.LONGITUDINAL_HARNESS_UPGRADE


def test_rivian_park_fully_disables_mads():
  mads, CS = build_mads(GearShifter.park)

  mads.update_events(CS)
  enabled, active = mads.state_machine.update()

  assert mads.events_sp.has(EventNameSP.lkasDisable)
  assert not mads.events_sp.has(EventNameSP.silentLkasDisable)
  assert mads.events.has(EventName.wrongGear)
  assert mads.state_machine.state == State.disabled
  assert not enabled
  assert not active


def test_rivian_reverse_retains_paused_behavior():
  mads, CS = build_mads(GearShifter.reverse)

  mads.update_events(CS)
  enabled, active = mads.state_machine.update()

  assert mads.events_sp.has(EventNameSP.silentLkasDisable)
  assert mads.events_sp.has(EventNameSP.silentWrongGear)
  assert mads.state_machine.state == State.paused
  assert enabled
  assert not active


def test_rivian_scroll_long_press_disables_lateral_and_longitudinal():
  mads, CS = build_mads(GearShifter.drive)
  mads.selfdrive.enabled = True
  CS.buttonEvents = [structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

  mads.add_rivian_scroll_event(CS)
  assert mads.events.has(EventName.buttonCancel)

  mads.selfdrive.enabled = False  # main state machine consumes buttonCancel first
  mads.update_events(CS)
  enabled, active = mads.state_machine.update()

  assert mads.events_sp.has(EventNameSP.lkasDisable)
  assert not enabled
  assert not active


def test_rivian_scroll_long_press_disables_mads_only():
  mads, CS = build_mads(GearShifter.drive)
  CS.buttonEvents = [structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

  mads.add_rivian_scroll_event(CS)
  assert not mads.events.has(EventName.buttonCancel)
  mads.update_events(CS)
  enabled, active = mads.state_machine.update()

  assert mads.events_sp.has(EventNameSP.lkasDisable)
  assert not enabled
  assert not active


def test_rivian_scroll_long_press_disables_paused_or_overriding_mads():
  for initial_state in (State.paused, State.overriding):
    mads, CS = build_mads(GearShifter.drive)
    mads.state_machine.state = initial_state
    CS.buttonEvents = [structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

    mads.add_rivian_scroll_event(CS)
    mads.update_events(CS)
    enabled, active = mads.state_machine.update()

    assert mads.events_sp.has(EventNameSP.lkasDisable)
    assert not enabled
    assert not active


def test_rivian_scroll_long_press_enables_mads_only():
  mads, CS = build_mads(GearShifter.drive)
  mads.enabled = False
  mads.active = False
  mads.state_machine.state = State.disabled
  CS.buttonEvents = [structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

  mads.add_rivian_scroll_event(CS)
  mads.update_events(CS)
  enabled, active = mads.state_machine.update()

  assert not mads.events.has(EventName.buttonCancel)
  assert mads.events_sp.has(EventNameSP.lkasEnable)
  assert not mads.events_sp.has(EventNameSP.lkasDisable)
  assert enabled
  assert active


def test_rivian_scroll_long_press_does_not_enable_mads_after_full_disengagement():
  mads, CS = build_mads(GearShifter.drive)
  mads.enabled = False
  mads.active = False
  mads.state_machine.state = State.disabled
  mads.selfdrive.enabled = True
  mads.selfdrive.enabled_prev = True
  CS.buttonEvents = [structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

  mads.add_rivian_scroll_event(CS)
  assert mads.events.has(EventName.buttonCancel)

  mads.selfdrive.enabled = False  # main state machine consumes buttonCancel first
  mads.update_events(CS)

  assert not mads.events_sp.has(EventNameSP.lkasEnable)
  assert not mads.events_sp.has(EventNameSP.lkasDisable)


def test_rivian_scroll_long_press_ignored_with_mads_disabled():
  mads, CS = build_mads(GearShifter.drive)
  mads.enabled = False
  mads.active = False
  mads.enabled_toggle = False
  mads.state_machine.state = State.disabled
  CS.buttonEvents = [structs.CarState.ButtonEvent(pressed=True, type=ButtonType.lkas)]

  mads.add_rivian_scroll_event(CS)

  assert not mads.events.has(EventName.buttonCancel)
