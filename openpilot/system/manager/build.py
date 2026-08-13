#!/usr/bin/env python3
import os
import subprocess
import json

# NOTE: Do NOT import anything here that needs be built (e.g. params)
from openpilot.common.basedir import BASEDIR
from openpilot.common.spinner import Spinner
from openpilot.common.text_window import TextWindow
from openpilot.common.hardware import HARDWARE, AGNOS
from openpilot.selfdrive.modeld.fetch_compiled_models import fetch_targets
from openpilot.selfdrive.modeld.helpers import chestnut_present


def fetch_default_models() -> dict:
  """Fetch compatible default artifacts, leaving SCons as the fallback."""
  targets = ["small", "dm"]
  if chestnut_present():
    targets.append("big")
  try:
    result = fetch_targets(BASEDIR, targets)
  except Exception as e:
    result = {"results": [{"target": target, "status": "remote_unavailable", "error": str(e)} for target in targets],
              "skip": dict.fromkeys(targets, False)}
  for model in result["results"]:
    detail = model.get("error", "")
    suffix = f" ({detail})" if detail else ""
    identity = ""
    if model.get("onnx_sha256") and model.get("tinygrad_ref"):
      identity = f" [{model['onnx_sha256'][:8]}/{model['tinygrad_ref'][:8]}]"
    fallback = " (local SCons fallback)" if model["status"] not in ("cache_hit", "remote_hit") else ""
    print(f"[MODEL] {model['target']}: {model['status']}{identity}{fallback}{suffix}")
  return result

def build() -> None:
  spinner = Spinner()
  spinner.update_progress(0, 100)

  HARDWARE.set_power_save(False)
  if AGNOS:
    os.sched_setaffinity(0, range(8))  # ensure we can use the isolcpus cores

  # Host/CI builds use their own model-generation workflows. Fetching the
  # comma-native artifacts is only meaningful on the AGNOS device build.
  model_fetch = fetch_default_models() if AGNOS and os.getenv("SKIP_MODEL_FETCH") != "1" else {"results": [], "skip": {}}
  model_env = {
    f"SKIP_{target.upper()}_MODEL_COMPILE": "1"
    for target, skip in model_fetch.get("skip", {}).items() if skip
  }

  # building with all cores can result in using too much memory, so retry serially
  compile_output: list[bytes] = []
  for parallelism in ([], ["-j4"], ["-j1"]):
    compile_output.clear()
    with subprocess.Popen(["scons", *parallelism], cwd=BASEDIR,
                          env={**os.environ, **model_env, "PWD": BASEDIR}, stderr=subprocess.PIPE) as scons:
      assert scons.stderr is not None

      # Read progress from stderr and update spinner
      while scons.poll() is None:
        try:
          line = scons.stderr.readline()
          if line is None:
            continue
          line = line.rstrip()

          prefix = b'progress: '
          if line.startswith(prefix):
            progress = float(line[len(prefix):])
            spinner.update_progress(100 * min(1., progress / 100.), 100.)
          elif len(line):
            compile_output.append(line)
            print(line.decode('utf8', 'replace'))
        except Exception:
          pass

      # Drain and close the pipe before retrying or returning.
      for line in scons.stderr.read().split(b'\n'):
        line = line.rstrip()
        if len(line):
          compile_output.append(line)

    if scons.returncode == 0:
      break

  os.sync()

  if scons.returncode != 0:
    # Build failed log errors
    error_s = b"\n".join(compile_output).decode('utf8', 'replace')

    # Show TextWindow
    spinner.close()
    if not os.getenv("CI"):
      with TextWindow("openpilot failed to build\n \n" + error_s) as t:
        t.wait_for_exit()
    exit(1)

  # Auto-prebuilt packaging must be able to prove that this exact source commit
  # completed the normal device build, not merely find binaries from an older checkout.
  commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASEDIR, text=True).strip()
  marker = os.getenv("OPENPILOT_BUILD_MARKER", "/tmp/openpilot-build.json")
  with open(marker, "w") as f:
    json.dump({"commit": commit, "models": model_fetch.get("results", [])}, f)

if __name__ == "__main__":
  build()
