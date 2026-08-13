from pathlib import Path

from openpilot.system.manager import build


def test_fetch_default_models_fetches_all_targets(monkeypatch):
  def fetch_targets(repo_root, targets):
    assert repo_root == Path(build.BASEDIR)
    assert targets == ["small", "dm", "big"]
    return {"results": [], "skip": {}}

  monkeypatch.setattr(build, "fetch_targets", fetch_targets)

  assert build.fetch_default_models() == {"results": [], "skip": {}}
