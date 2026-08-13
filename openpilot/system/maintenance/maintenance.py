#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.selfdrived.alertmanager import set_offroad_alert


CONFIG_PATH = Path(__file__).with_name("baseline.json")
STATE_PATH = Path(os.getenv("MAINTENANCE_STATE_PATH", "/data/baseline-update.json"))
PREBUILT_BLOCKER = Path(os.getenv("PREBUILT_BLOCKER", "/tmp/openpilot-prebuilt.block"))
PREBUILT_WORK_GLOB = "openpilot-prebuilt.*"
DEFAULT_SSH_KEY = Path(os.getenv("PREBUILT_GITHUB_SSH_KEY", "/data/ssh/prebuilt-deploy-key"))
GITHUB_KNOWN_HOST = "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"

CMD_PARAM = "MaintenanceCommand"
STATE_PARAM = "MaintenanceState"
PROGRESS_PARAM = "MaintenanceProgress"
DETAIL_PARAM = "MaintenanceDetail"
OPERATION_PARAM = "MaintenanceOperation"
AUTO_READY_PARAM = "AutoPrebuiltReady"
AUTO_DETAIL_PARAM = "AutoPrebuiltDetail"
BASELINE_READY_PARAM = "BaselineUpdateReady"
BASELINE_DETAIL_PARAM = "BaselineUpdateDetail"
BASELINE_AVAILABLE_PARAM = "BaselineUpdateAvailable"
BUILD_MARKER = Path(os.getenv("OPENPILOT_BUILD_MARKER", "/tmp/openpilot-build.json"))


def git(args: list[str], cwd: str = BASEDIR, env: dict[str, str] | None = None) -> str:
  git_env = (env or os.environ).copy()
  # Eligibility checks run continuously and must not race updater snapshots by
  # briefly creating an optional .git/index.lock.
  git_env["GIT_OPTIONAL_LOCKS"] = "0"
  return subprocess.check_output(["git", *args], cwd=cwd, env=git_env, stderr=subprocess.STDOUT, text=True).strip()


def load_config(path: Path = CONFIG_PATH) -> dict[str, str]:
  config = json.loads(path.read_text())
  if set(config) != {"remote_url", "branch", "sha"}:
    raise ValueError("baseline config must contain remote_url, branch, and sha")
  git(["check-ref-format", "--branch", config["branch"]])
  if len(config["sha"]) != 40 or any(c not in "0123456789abcdefABCDEF" for c in config["sha"]):
    raise ValueError("baseline sha must be a full 40-character Git SHA")
  return config


def atomic_json(path: Path, value: dict) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  try:
    with os.fdopen(fd, "w") as f:
      json.dump(value, f, sort_keys=True)
      f.flush()
      os.fsync(f.fileno())
    os.replace(tmp, path)
  finally:
    try:
      os.unlink(tmp)
    except FileNotFoundError:
      pass


def maintenance_blocked(state_path: Path = STATE_PATH, blocker: Path = PREBUILT_BLOCKER,
                        work_parent: Path = Path("/data")) -> bool:
  return state_path.exists() or blocker.exists() or any(work_parent.glob(PREBUILT_WORK_GLOB))


def commit_date(ref: str, cwd: str = BASEDIR) -> str:
  timestamp = int(git(["show", "-s", "--format=%ct", ref], cwd))
  return datetime.datetime.fromtimestamp(timestamp, datetime.UTC).strftime("%y%m%d")


def provenance_tags(source_branch: str, source_ref: str, baseline_branch: str, baseline_ref: str,
                    cwd: str = BASEDIR) -> tuple[str, str]:
  baseline_tag = f"{baseline_branch}@{commit_date(baseline_ref, cwd)}"
  source_tag = f"{source_branch}@{commit_date(source_ref, cwd)}.{baseline_tag}"
  return baseline_tag, source_tag


def source_branch(current_branch: str, prebuilt: bool) -> str:
  return f"{current_branch}-src" if prebuilt else current_branch


@dataclass(frozen=True)
class Eligibility:
  ready: bool
  reason: str


def auto_prebuilt_eligibility(cwd: str = BASEDIR, offroad: bool = True) -> Eligibility:
  if not offroad:
    return Eligibility(False, "device is on road")
  if Path(cwd, "prebuilt").exists():
    return Eligibility(False, "current checkout is already a prebuilt")
  if not git(["branch", "--show-current"], cwd).endswith("-src"):
    return Eligibility(False, "source branch name must end in -src")
  if git(["status", "--porcelain", "--untracked-files=no"], cwd):
    return Eligibility(False, "checkout or submodules are dirty")
  if any(line.startswith("-") for line in git(["submodule", "status", "--recursive"], cwd).splitlines()):
    return Eligibility(False, "submodules are not initialized")
  head = git(["rev-parse", "HEAD"], cwd)
  try:
    if json.loads(BUILD_MARKER.read_text()).get("commit") != head:
      return Eligibility(False, "current commit has not completed compilation")
  except (FileNotFoundError, json.JSONDecodeError, OSError):
    return Eligibility(False, "current commit has not completed compilation")
  refs = git(["for-each-ref", "--format=%(refname)", "--contains", head, "refs/remotes/origin/"], cwd)
  if not refs:
    return Eligibility(False, "commit is not present on origin")
  try:
    subprocess.check_call(["pgrep", "-f", r"(^|/| )build\.py($| )|[s]cons"], stdout=subprocess.DEVNULL)
    return Eligibility(False, "build is still running")
  except subprocess.CalledProcessError:
    pass
  for binary in ("openpilot/system/camerad/camerad", "openpilot/system/loggerd/loggerd", "openpilot/selfdrive/pandad/pandad"):
    path = Path(cwd, binary)
    if not path.is_file() or not os.access(path, os.X_OK):
      return Eligibility(False, f"missing compiled binary: {binary}")
    if "ARM aarch64" not in subprocess.check_output(["file", str(path)], text=True):
      return Eligibility(False, f"compiled binary is not ARM64: {binary}")
    ldd = subprocess.run(["ldd", str(path)], capture_output=True, text=True)
    if ldd.returncode != 0 or "not found" in ldd.stdout + ldd.stderr:
      return Eligibility(False, f"compiled binary has unresolved libraries: {binary}")
  return Eligibility(True, "ready")


class Maintenance:
  def __init__(self, params: Params | None = None, cwd: str = BASEDIR):
    self.params = params or Params()
    self.cwd = cwd
    self.config_path = Path(cwd, CONFIG_PATH.relative_to(BASEDIR))

  def status(self, state: str, progress: int, detail: str = "") -> None:
    self.params.put(STATE_PARAM, state, block=True)
    self.params.put(PROGRESS_PARAM, progress, block=True)
    self.params.put(DETAIL_PARAM, detail, block=True)
    if state == "idle":
      self.params.put(OPERATION_PARAM, "", block=True)

  def ssh_env(self) -> tuple[dict[str, str], str]:
    known_hosts = tempfile.NamedTemporaryFile(mode="w", prefix="github-known-hosts.", delete=False)
    known_hosts.write(GITHUB_KNOWN_HOST + "\n")
    known_hosts.close()
    os.chmod(known_hosts.name, 0o600)
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = " ".join((f"ssh -i {DEFAULT_SSH_KEY}", "-o IdentitiesOnly=yes", "-o StrictHostKeyChecking=yes",
                                       f"-o UserKnownHostsFile={known_hosts.name}", "-o GlobalKnownHostsFile=/dev/null"))
    return env, known_hosts.name

  def start_prebuilt(self) -> None:
    eligibility = auto_prebuilt_eligibility(self.cwd, self.params.get_bool("IsOffroad"))
    if not eligibility.ready:
      raise RuntimeError(eligibility.reason)
    self.params.put(OPERATION_PARAM, "prebuilt", block=True)
    self.status("prebuilt", 5, "creating on-road blocker")
    PREBUILT_BLOCKER.touch(exist_ok=False)
    env = os.environ.copy()
    env["PREBUILT_BLOCKER"] = str(PREBUILT_BLOCKER)
    # Failures intentionally retain the volatile blocker until reboot.
    self.status("prebuilt", 15, "packaging compiled checkout")
    try:
      subprocess.check_output(["release/create_mici_prebuilt.sh"], cwd=self.cwd, env=env,
                              stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
      output = (e.output or "").strip()
      raise RuntimeError(output or f"prebuilt generation exited with status {e.returncode}") from e
    finally:
      # Ignore commands queued by repeated taps while packaging was still active.
      self.params.remove(CMD_PARAM)
    self.status("rebooting", 100, "activating generated prebuilt")
    PREBUILT_BLOCKER.unlink(missing_ok=True)
    self.params.put_bool("DoReboot", True, block=True)

  def check_baseline(self) -> None:
    ready = self.params.get_bool("IsOffroad") and DEFAULT_SSH_KEY.is_file()
    self.params.put_bool(BASELINE_READY_PARAM, ready, block=True)
    if not ready:
      reason = "device is on road" if not self.params.get_bool("IsOffroad") else "persistent GitHub credential is missing"
      self.params.put(BASELINE_DETAIL_PARAM, reason, block=True)
      return
    config = load_config(self.config_path)
    tracking_ref = f"refs/remotes/baseline/{config['branch']}"
    git(["fetch", "--force", config["remote_url"], f"refs/heads/{config['branch']}:{tracking_ref}"], self.cwd)
    tip = git(["rev-parse", tracking_ref], self.cwd)
    available = tip != config["sha"]
    self.params.put(BASELINE_DETAIL_PARAM, "new baseline available" if available else "baseline is current", block=True)
    self.params.put_bool(BASELINE_AVAILABLE_PARAM, available, block=True)
    set_offroad_alert("Offroad_BaselineUpdate", available,
                      extra_text=f"{config['branch']} {tip[:8]}" if available else None)

  def start_baseline(self) -> None:
    if not self.params.get_bool("IsOffroad") or not DEFAULT_SSH_KEY.is_file():
      raise RuntimeError("baseline update requires off-road mode and the persistent GitHub credential")
    self.params.put(OPERATION_PARAM, "baseline", block=True)
    config = load_config(self.config_path)
    current = git(["branch", "--show-current"], self.cwd)
    branch = source_branch(current, Path(self.cwd, "prebuilt").exists())
    try:
      original_source_tip = git(["rev-parse", f"refs/remotes/origin/{branch}"], self.cwd)
    except subprocess.CalledProcessError as e:
      raise RuntimeError(f"origin does not advertise source branch {branch}") from e
    state = {"operation": "baseline", "stage": "switch", "source_branch": branch,
             "original_branch": current, "original_commit": git(["rev-parse", "HEAD"], self.cwd),
             "original_source_tip": original_source_tip, **config}
    atomic_json(STATE_PATH, state)
    self.resume_baseline()

  def resume_baseline(self) -> None:
    self.params.put(OPERATION_PARAM, "baseline", block=True)
    state = json.loads(STATE_PATH.read_text())
    if state.get("stage") == "failed":
      return
    branch = state["source_branch"]
    current_branch = git(["branch", "--show-current"], self.cwd)
    current_commit = git(["rev-parse", "HEAD"], self.cwd)
    target_branch = branch[:-4] if branch.endswith("-src") else ""
    if state.get("stage") == "prebuilt" and target_branch and current_branch == target_branch and Path(self.cwd, "prebuilt").exists():
      STATE_PATH.unlink()
      PREBUILT_BLOCKER.unlink(missing_ok=True)
      self.status("rebooting", 100, "activating generated prebuilt")
      self.params.put_bool("DoReboot", True, block=True)
      return

    source_switch_stage = state.get("stage") in ("switch", "awaiting_source_reboot")
    if current_branch != branch or (source_switch_stage and current_commit != state["original_source_tip"]):
      if state.get("stage") != "awaiting_source_reboot":
        self.status("baseline", 10, f"installing {branch}")
        self.params.put("UpdaterTargetBranch", branch, block=True)
        subprocess.run(["pkill", "-SIGHUP", "-f", "openpilot.system.updated.updated"], check=False)
        state["stage"] = "awaiting_source_reboot"
        atomic_json(STATE_PATH, state)
      elif self.params.get_bool("UpdateAvailable"):
        self.status("rebooting", 20, f"activating {branch}")
        self.params.put_bool("DoReboot", True, block=True)
      return

    if state.get("stage") == "prebuilt":
      PREBUILT_BLOCKER.unlink(missing_ok=True)
      self.start_prebuilt()
      STATE_PATH.unlink(missing_ok=True)
      return

    env, known_hosts = self.ssh_env()
    try:
      if state.get("stage") in ("switch", "awaiting_source_reboot", "rebasing"):
        config_path = self.config_path
        adopted_sha = load_config(config_path)["sha"]
        # If the process stopped after committing the config, continue at publish rather than replaying the rebase.
        already_rebased = state.get("new_baseline") is not None and adopted_sha == state["new_baseline"]
        if already_rebased:
          new_baseline = state["new_baseline"]
        else:
          if Path(self.cwd, ".git", "rebase-merge").exists() or Path(self.cwd, ".git", "rebase-apply").exists():
            git(["rebase", "--abort"], self.cwd)
          if git(["status", "--porcelain"], self.cwd):
            raise RuntimeError("source checkout is not pristine")
          self.status("baseline", 25, "fetching baseline")
          git(["fetch", state["remote_url"], state["branch"]], self.cwd, env)
          new_baseline = git(["rev-parse", "FETCH_HEAD"], self.cwd)
          state.update(stage="rebasing", new_baseline=new_baseline)
          atomic_json(STATE_PATH, state)
          self.status("baseline", 45, "rebasing source commits")
          try:
            git(["rebase", "--onto", new_baseline, state["sha"]], self.cwd)
          except subprocess.CalledProcessError as rebase_error:
            if not Path(self.cwd, ".git", "rebase-merge").exists() and not Path(self.cwd, ".git", "rebase-apply").exists():
              raise
            git(["rebase", "--abort"], self.cwd)
            if git(["status", "--porcelain"], self.cwd):
              raise RuntimeError("rebase conflicted and abort did not restore a pristine checkout") from rebase_error
            set_offroad_alert("Offroad_BaselineConflict", True)
            STATE_PATH.unlink()
            self.status("idle", 0, "merge conflicts require manual patching")
            return

          # Record the adopted baseline in the release packaged by this rewritten source.
          config = {"remote_url": state["remote_url"], "branch": state["branch"], "sha": new_baseline}
          config_path.write_text(json.dumps(config, indent=2) + "\n")
          git(["add", str(config_path.relative_to(self.cwd))], self.cwd)
          if git(["rev-parse", "HEAD"], self.cwd) == new_baseline:
            git(["commit", "-m", "Update baseline configuration"], self.cwd)
          else:
            git(["commit", "--amend", "--no-edit"], self.cwd)

        source_tip = git(["rev-parse", "HEAD"], self.cwd)
        baseline_tag, source_tag = provenance_tags(branch, source_tip, state["branch"], new_baseline, self.cwd)
        state.update(stage="publishing", source_tip=source_tip, baseline_tag=baseline_tag, source_tag=source_tag)
        atomic_json(STATE_PATH, state)

      source_tip = state["source_tip"]
      new_baseline = state["new_baseline"]
      baseline_tag = state["baseline_tag"]
      source_tag = state["source_tag"]
      self.status("baseline", 65, "tagging and publishing source")
      for tag, ref in ((baseline_tag, new_baseline), (source_tag, source_tip)):
        git(["tag", "-fa", tag, ref, "-m", tag], self.cwd)
      origin = git(["remote", "get-url", "--push", "origin"], self.cwd)
      git(["push", "--force", origin, f"HEAD:refs/heads/{branch}",
           f"refs/tags/{baseline_tag}:refs/tags/{baseline_tag}", f"refs/tags/{source_tag}:refs/tags/{source_tag}"], self.cwd, env)
      published = {ref: sha for sha, ref in (line.split() for line in git(["ls-remote", origin,
                                                                          f"refs/heads/{branch}", f"refs/tags/{baseline_tag}^{{}}",
                                                                          f"refs/tags/{source_tag}^{{}}"], self.cwd, env).splitlines())}
      expected = {f"refs/heads/{branch}": source_tip, f"refs/tags/{baseline_tag}^{{}}": new_baseline,
                  f"refs/tags/{source_tag}^{{}}": source_tip}
      if published != expected:
        raise RuntimeError("published baseline refs failed remote verification")
      git(["update-ref", f"refs/remotes/origin/{branch}", source_tip], self.cwd)
      state["stage"] = "prebuilt"
      atomic_json(STATE_PATH, state)
      self.start_prebuilt()
      STATE_PATH.unlink(missing_ok=True)
    finally:
      os.unlink(known_hosts)

  def cancel(self) -> None:
    state = json.loads(STATE_PATH.read_text())
    subprocess.run(["git", "rebase", "--abort"], cwd=self.cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    branch = state["source_branch"]
    git(["fetch", "origin", branch], self.cwd)
    git(["checkout", "--force", "--no-recurse-submodules", "-B", branch, state["original_source_tip"]], self.cwd)
    git(["clean", "-xdff"], self.cwd)
    if git(["status", "--porcelain"], self.cwd):
      raise RuntimeError("cancel could not restore a pristine source checkout")
    STATE_PATH.unlink()
    self.status("idle", 0, "")

  def run_command(self, command: str) -> None:
    if command == "prebuilt":
      self.start_prebuilt()
    elif command == "baseline":
      self.start_baseline()
    elif command == "retry":
      state = json.loads(STATE_PATH.read_text())
      state["stage"] = state.pop("resume_stage", "rebasing")
      state.pop("error", None)
      atomic_json(STATE_PATH, state)
      self.resume_baseline()
    elif command == "cancel":
      self.cancel()
    else:
      raise ValueError(f"unknown maintenance command: {command}")


def main() -> None:
  params = Params()
  maintenance = Maintenance(params)
  maintenance.status("idle", 0)
  last_check = 0.0
  while True:
    try:
      if STATE_PATH.exists():
        maintenance.resume_baseline()
      command = params.get(CMD_PARAM)
      if command:
        params.remove(CMD_PARAM)
        maintenance.run_command(command)
      if time.monotonic() - last_check > 15 * 60:
        maintenance.check_baseline()
        last_check = time.monotonic()
      eligibility = auto_prebuilt_eligibility(BASEDIR, params.get_bool("IsOffroad"))
      params.put_bool(AUTO_READY_PARAM, eligibility.ready)
      params.put(AUTO_DETAIL_PARAM, eligibility.reason)
      if params.get(STATE_PARAM) == "idle":
        params.put(DETAIL_PARAM, eligibility.reason)
    except Exception as e:
      cloudlog.exception("maintenance operation failed")
      if STATE_PATH.exists():
        try:
          state = json.loads(STATE_PATH.read_text())
          if state.get("stage") != "failed":
            state.update(resume_stage=state.get("stage", "rebasing"), stage="failed", error=str(e))
            atomic_json(STATE_PATH, state)
        except Exception:
          cloudlog.exception("failed to persist maintenance error state")
      maintenance.status("failed", 0, str(e))
    time.sleep(1)


if __name__ == "__main__":
  main()
