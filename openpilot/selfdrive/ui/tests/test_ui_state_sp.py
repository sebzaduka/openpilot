from opendbc.car.structs import car
from openpilot.common.params import Params
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.ui.sunnypilot.ui_state import UIStateSP


class TestUIStateSP(OpenpilotTestCase):
  def setup_method(self):
    self.params = Params()
    self.params.put_bool("AlphaLongitudinalEnabled", True, block=True)

    self.ui_state_sp = UIStateSP.__new__(UIStateSP)
    self.ui_state_sp.params = self.params
    self.ui_state_sp.CP_SP = None
    self.ui_state_sp.has_longitudinal_control = False

  def test_alpha_longitudinal_persists_without_car_params(self):
    self.ui_state_sp.CP = None

    self.ui_state_sp._enforce_constraints()

    assert self.params.get_bool("AlphaLongitudinalEnabled")

  def test_alpha_longitudinal_persists_when_unavailable(self):
    self.ui_state_sp.CP = car.CarParams.new_message(alphaLongitudinalAvailable=False)

    self.ui_state_sp._enforce_constraints()

    assert self.params.get_bool("AlphaLongitudinalEnabled")
