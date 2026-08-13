from openpilot.system.manager import build
from openpilot.selfdrive.modeld import compiled_model_artifacts


def test_native_build_has_no_remote_model_fetcher():
  assert not hasattr(build, "fetch_default_models")
  assert not hasattr(build, "fetch_targets")
  assert not hasattr(compiled_model_artifacts, "fetch_targets")
  assert not hasattr(compiled_model_artifacts, "resolve_remote")
