import os
import subprocess

import pytest

from openpilot.common.basedir import BASEDIR


LAUNCH_ENV = os.path.join(BASEDIR, "launch_env.sh")
READ_POWER_LIMIT = r'''
source "$1"
bash -c 'if test -n "${AM_POWER_LIMIT+x}"; then printf "set:%s" "$AM_POWER_LIMIT"; else printf unset; fi'
'''


def source_launch_env(power_limit_file, power_limit=None):
  env = os.environ.copy()
  env.pop("AM_POWER_LIMIT", None)
  env["AM_POWER_LIMIT_FILE"] = os.fspath(power_limit_file)
  if power_limit is not None:
    env["AM_POWER_LIMIT"] = power_limit

  result = subprocess.run(["bash", "-c", READ_POWER_LIMIT, "bash", LAUNCH_ENV],
                          check=True, capture_output=True, env=env, text=True)
  return result.stdout


def test_power_limit_file_is_exported(tmp_path):
  power_limit_file = tmp_path / "power-limit"
  power_limit_file.write_text("80\n")

  assert source_launch_env(power_limit_file) == "set:80"


@pytest.mark.parametrize("contents", [None, ""])
def test_missing_or_empty_power_limit_file_is_ignored(tmp_path, contents):
  power_limit_file = tmp_path / "power-limit"
  if contents is not None:
    power_limit_file.write_text(contents)

  assert source_launch_env(power_limit_file) == "unset"


@pytest.mark.parametrize("explicit_value", ["90", ""])
def test_explicit_power_limit_takes_precedence(tmp_path, explicit_value):
  power_limit_file = tmp_path / "power-limit"
  power_limit_file.write_text("80\n")

  assert source_launch_env(power_limit_file, explicit_value) == f"set:{explicit_value}"
