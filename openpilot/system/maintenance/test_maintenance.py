import json
import os
import subprocess
from pathlib import Path

import pytest

import openpilot.system.maintenance.maintenance as maintenance_module
from openpilot.system.maintenance.maintenance import (CMD_PARAM, CONFIG_PATH, Eligibility, Maintenance, atomic_json, commit_date, load_config,
                                                      github_https_remote, maintenance_blocked, provenance_tags, source_branch)


def run(repo: Path, *args: str, env=None) -> str:
  return subprocess.check_output(["git", *args], cwd=repo, env=env, text=True).strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
  run(tmp_path, "init", "-q")
  run(tmp_path, "config", "user.name", "Test")
  run(tmp_path, "config", "user.email", "test@example.com")
  (tmp_path / "file").write_text("one")
  run(tmp_path, "add", "file")
  env = os.environ | {"GIT_AUTHOR_DATE": "2026-08-11T23:00:00Z", "GIT_COMMITTER_DATE": "2026-08-11T23:00:00Z"}
  run(tmp_path, "commit", "-qm", "baseline", env=env)
  return tmp_path


def test_config_validation(tmp_path: Path):
  path = tmp_path / "baseline.json"
  path.write_text(json.dumps({"remote_url": "https://example.test/repo", "branch": "rx-dev-src", "sha": "a" * 40}))
  assert load_config(path)["branch"] == "rx-dev-src"
  path.write_text(json.dumps({"remote_url": "x", "branch": "bad branch", "sha": "a" * 40}))
  with pytest.raises(subprocess.CalledProcessError):
    load_config(path)


def test_provenance_tags_use_utc_committer_dates(repo: Path):
  baseline = run(repo, "rev-parse", "HEAD")
  (repo / "file").write_text("two")
  run(repo, "commit", "-qam", "source")
  source = run(repo, "rev-parse", "HEAD")
  assert commit_date(baseline, str(repo)) == "260811"
  assert provenance_tags("device-src", source, "upstream-src", baseline, str(repo)) == (
    "upstream-src@260811", f"device-src@{commit_date(source, str(repo))}.upstream-src@260811")


def test_source_branch():
  assert source_branch("device", True) == "device-src"
  assert source_branch("device-src", False) == "device-src"


def test_github_remote_uses_https_without_rewriting_local_remotes():
  assert github_https_remote("git@github.com:owner/repo.git") == "https://github.com/owner/repo.git"
  assert github_https_remote("ssh://git@github.com/owner/repo.git") == "https://github.com/owner/repo.git"
  local = "/tmp/origin.git"
  assert github_https_remote(local) == local


def test_model_artifact_eligibility_requires_chestnut_big_model(tmp_path: Path, monkeypatch):
  monkeypatch.setattr(maintenance_module, "chestnut_present", lambda: True)
  def validate(repo_root, destination, targets):
    assert targets == ["small", "dm", "big"]
    return {"valid": False, "results": [{"target": "big", "valid": False, "detail": "missing big model"}]}
  monkeypatch.setattr(maintenance_module, "validate_compatible_targets", validate)
  result = maintenance_module.model_artifact_eligibility(str(tmp_path))
  assert not result.ready
  assert "big" in result.reason


def test_atomic_state_and_blockers(tmp_path: Path):
  state = tmp_path / "state.json"
  blocker = tmp_path / "blocker"
  work = tmp_path / "data"
  work.mkdir()
  atomic_json(state, {"stage": "rebase"})
  assert json.loads(state.read_text()) == {"stage": "rebase"}
  assert maintenance_blocked(state, blocker, work)
  state.unlink()
  blocker.touch()
  assert maintenance_blocked(state, blocker, work)
  blocker.unlink()
  (work / "openpilot-prebuilt.123").mkdir()
  assert maintenance_blocked(state, blocker, work)


def test_git_disables_optional_locks(monkeypatch):
  observed = {}

  def check_output(*args, **kwargs):
    observed.update(kwargs)
    return ""

  monkeypatch.setattr(subprocess, "check_output", check_output)
  maintenance_module.git(["status"])

  assert observed["env"]["GIT_OPTIONAL_LOCKS"] == "0"


class FakeParams:
  def __init__(self):
    self.values = {"IsOffroad": True}

  def get_bool(self, key):
    return bool(self.values.get(key, False))

  def get(self, key):
    return self.values.get(key)

  def put(self, key, value, block=False):
    self.values[key] = value

  def put_bool(self, key, value, block=False):
    self.values[key] = value

  def remove(self, key):
    self.values.pop(key, None)


def test_status_writes_typed_progress():
  params = FakeParams()
  operation = Maintenance(params)

  operation.status("prebuilt", 15, "packaging compiled checkout")

  assert params.values["MaintenanceState"] == "prebuilt"
  assert params.values["MaintenanceProgress"] == 15
  assert type(params.values["MaintenanceProgress"]) is int
  assert params.values["MaintenanceDetail"] == "packaging compiled checkout"


def test_prebuilt_failure_preserves_script_output_and_discards_queued_command(tmp_path: Path, monkeypatch):
  params = FakeParams()
  blocker = tmp_path / "prebuilt.block"
  monkeypatch.setattr(maintenance_module, "PREBUILT_BLOCKER", blocker)
  monkeypatch.setattr(maintenance_module, "auto_prebuilt_eligibility", lambda cwd, offroad: Eligibility(True, "ready"))

  def fail_prebuilt(*args, **kwargs):
    params.put(CMD_PARAM, "prebuilt")
    raise subprocess.CalledProcessError(23, args[0], output="rsync: release file vanished\n")

  monkeypatch.setattr(subprocess, "check_output", fail_prebuilt)

  with pytest.raises(RuntimeError, match="rsync: release file vanished"):
    Maintenance(params, str(tmp_path)).start_prebuilt()

  assert blocker.exists()
  assert CMD_PARAM not in params.values


def test_prebuilt_failure_without_output_reports_exit_status(tmp_path: Path, monkeypatch):
  params = FakeParams()
  monkeypatch.setattr(maintenance_module, "PREBUILT_BLOCKER", tmp_path / "prebuilt.block")
  monkeypatch.setattr(maintenance_module, "auto_prebuilt_eligibility", lambda cwd, offroad: Eligibility(True, "ready"))
  monkeypatch.setattr(subprocess, "check_output",
                      lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.CalledProcessError(1, args[0])))

  with pytest.raises(RuntimeError, match="prebuilt generation exited with status 1"):
    Maintenance(params, str(tmp_path)).start_prebuilt()


def test_successful_baseline_rebase_tags_and_push(tmp_path: Path, monkeypatch):
  baseline = tmp_path / "baseline"
  baseline.mkdir()
  run(baseline, "init", "-q", "-b", "rx-dev-src")
  run(baseline, "config", "user.name", "Test")
  run(baseline, "config", "user.email", "test@example.com")
  (baseline / "base").write_text("old")
  run(baseline, "add", "base")
  run(baseline, "commit", "-qm", "old baseline")
  old_baseline = run(baseline, "rev-parse", "HEAD")
  (baseline / "base").write_text("new")
  run(baseline, "commit", "-qam", "new baseline")
  new_baseline = run(baseline, "rev-parse", "HEAD")

  source_seed = tmp_path / "source-seed"
  run(tmp_path, "clone", "-q", str(baseline), str(source_seed))
  run(source_seed, "checkout", "-qb", "device-src", old_baseline)
  run(source_seed, "config", "user.name", "Test")
  run(source_seed, "config", "user.email", "test@example.com")
  relative_config = CONFIG_PATH.relative_to(maintenance_module.BASEDIR)
  config_path = source_seed / relative_config
  config_path.parent.mkdir(parents=True)
  config_path.write_text(json.dumps({"remote_url": str(baseline), "branch": "rx-dev-src", "sha": old_baseline}) + "\n")
  (source_seed / "patch").write_text("local change")
  run(source_seed, "add", ".")
  run(source_seed, "commit", "-qm", "source patch")

  origin = tmp_path / "origin.git"
  run(tmp_path, "clone", "-q", "--bare", str(source_seed), str(origin))
  work = tmp_path / "work"
  run(tmp_path, "clone", "-q", "-b", "device-src", str(origin), str(work))
  run(work, "config", "user.name", "Test")
  run(work, "config", "user.email", "test@example.com")

  state_path = tmp_path / "state.json"
  key = tmp_path / "github-token"
  key.write_text("token\n")
  monkeypatch.setattr(maintenance_module, "STATE_PATH", state_path)
  monkeypatch.setattr(maintenance_module, "DEFAULT_GITHUB_TOKEN", key)
  prebuilt_called = []
  monkeypatch.setattr(Maintenance, "start_prebuilt", lambda self: prebuilt_called.append(True))

  operation = Maintenance(FakeParams(), str(work))
  operation.start_baseline()

  assert prebuilt_called == [True]
  assert not state_path.exists()
  rewritten = run(work, "rev-parse", "HEAD")
  assert json.loads((work / relative_config).read_text())["sha"] == new_baseline
  assert run(work, "merge-base", "--is-ancestor", new_baseline, rewritten) == ""
  baseline_tag, source_tag = provenance_tags("device-src", rewritten, "rx-dev-src", new_baseline, str(work))
  assert run(work, "rev-parse", f"{baseline_tag}^{{}}") == new_baseline
  assert run(work, "rev-parse", f"{source_tag}^{{}}") == rewritten
  assert run(work, "ls-remote", origin, "refs/heads/device-src").split()[0] == rewritten
