#!/usr/bin/env python3
import os
import subprocess
import json
from pathlib import Path

# NOTE: Do NOT import anything here that needs be built (e.g. params)
from openpilot.common.basedir import BASEDIR
from openpilot.common.spinner import Spinner
from openpilot.common.text_window import TextWindow
from openpilot.common.hardware import HARDWARE, AGNOS
from openpilot.selfdrive.modeld.compiled_model_artifacts import validate_compatible_targets
from openpilot.selfdrive.modeld.helpers import chestnut_present

def build() -> None:
  spinner = Spinner()
  spinner.update_progress(0, 100)

  HARDWARE.set_power_save(False)
  if AGNOS:
    os.sched_setaffinity(0, range(8))  # ensure we can use the isolcpus cores
  chestnut_detected = chestnut_present() if AGNOS else False

  # building with all cores can result in using too much memory, so retry serially
  compile_output: list[bytes] = []
  for parallelism in ([], ["-j4"], ["-j1"]):
    compile_output.clear()
    with subprocess.Popen(["scons", *parallelism], cwd=BASEDIR,
                          env={**os.environ, "PWD": BASEDIR}, stderr=subprocess.PIPE) as scons:
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
  # completed the normal device build and which locally compiled model artifacts
  # that build produced. A source build may complete without Chestnut, but Auto
  # Prebuilt requires all three canonical targets.
  commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASEDIR, text=True).strip()
  model_validation = validate_compatible_targets(
    Path(BASEDIR), Path(BASEDIR) / "openpilot/selfdrive/modeld/models", ["small", "dm", "big"], required_source="local")
  marker = os.getenv("OPENPILOT_BUILD_MARKER", "/tmp/openpilot-build.json")
  with open(marker, "w") as f:
    json.dump({
      "schema": 1,
      "commit": commit,
      "artifact_policy": "local-only",
      "chestnut_detected": chestnut_detected,
      "models": model_validation["results"],
    }, f)

if __name__ == "__main__":
  build()
