from pathlib import Path

import openpilot.system.updated.updated as updated


def test_finalize_update_removes_copied_index_lock(tmp_path: Path, monkeypatch):
  merged = tmp_path / "merged"
  finalized = tmp_path / "finalized"
  (merged / ".git").mkdir(parents=True)
  (merged / ".git/index.lock").touch()

  monkeypatch.setattr(updated, "OVERLAY_MERGED", str(merged))
  monkeypatch.setattr(updated, "FINALIZED", str(finalized))

  commands = []

  def run(cmd, cwd=None):
    commands.append(cmd)
    assert not Path(cwd, ".git/index.lock").exists()
    return ""

  monkeypatch.setattr(updated, "run", run)

  updated.finalize_update()

  assert commands == [["git", "reset", "--hard"],
                      ["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"]]
  assert (finalized / ".overlay_consistent").exists()
