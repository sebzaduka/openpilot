#!/usr/bin/env python3
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestCommaPrebuiltContract(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.script = (ROOT / "release/create_mici_prebuilt.sh").read_text()

  def test_uses_provisioned_token_by_default(self):
    self.assertIn('if test "$#" -gt 1', self.script)
    self.assertIn('DEFAULT_TOKEN="${PREBUILT_GITHUB_TOKEN_FILE:-/data/prebuilt-publishing/github-token}"', self.script)
    self.assertIn('test -e "$DEFAULT_TOKEN" && PUBLISH=1', self.script)
    self.assertIn('--local-only) ;;', self.script)
    self.assertIn('GIT_ASKPASS_FILE=', self.script)
    self.assertNotIn('prebuilt-deploy-key', self.script)

  def test_uses_persistent_prebuilt_identity(self):
    self.assertIn('DEFAULT_GIT_IDENTITY="${PREBUILT_GIT_IDENTITY:-/data/prebuilt-publishing/gitconfig}"', self.script)
    self.assertIn('git config --file "$DEFAULT_GIT_IDENTITY" user.name', self.script)
    self.assertIn('git config --file "$DEFAULT_GIT_IDENTITY" user.email', self.script)
    self.assertNotIn('$(git config user.name', self.script)
    self.assertNotIn('$(git config user.email', self.script)
    self.assertIn('GIT_COMMITTER_NAME="$GIT_USER_NAME" GIT_COMMITTER_EMAIL="$GIT_USER_EMAIL"', self.script)

  def test_requires_native_completed_build(self):
    for contract in ('test "$(uname -m)" != aarch64', "test ! -f /AGNOS", "test ! -e /dev/ion", "pgrep -f"):
      self.assertIn(contract, self.script)
    self.assertIn('BUILD_MARKER="${OPENPILOT_BUILD_MARKER:-/tmp/openpilot-build.json}"', self.script)
    self.assertIn("release/validate_mici_prebuilt.sh", self.script)
    self.assertIn('cat /data/params/d/IsOffroad', self.script)
    self.assertNotIn("from openpilot.common.params import Params", self.script)

  def test_validates_default_models_before_packaging(self):
    self.assertIn("MODEL_TARGETS=(small dm)", self.script)
    self.assertIn("chestnut_present", self.script)
    self.assertIn("--validate --compatible --targets \"${MODEL_TARGETS[@]}\"", self.script)
    self.assertIn("VALIDATOR_ARGS+=(--require-big)", self.script)

  def test_packages_ignored_runtime_build_outputs(self):
    self.assertIn("git ls-files --others --ignored --exclude-standard -z", self.script)
    self.assertIn("git submodule foreach --recursive --quiet", self.script)
    self.assertIn('sed -z "s#^#$displaypath/#"', self.script)
    self.assertIn("sort -zu", self.script)
    self.assertIn('rsync -aR --from0 --files-from="$FILE_LIST"', self.script)

  def test_local_mode_does_not_publish(self):
    checkout_command = 'git checkout --force --no-recurse-submodules -B "$TARGET_BRANCH" "$RELEASE_COMMIT"'
    checkout = self.script.index(checkout_command)
    publish_guard = self.script.rindex('if test "$PUBLISH" -eq 1', 0, checkout)
    push = self.script.index("git -C \"$OUTPUT_DIR\" push")
    self.assertLess(publish_guard, push)
    self.assertLess(push, checkout)
    self.assertIn("git clean -xdff", self.script[checkout:])
    self.assertIn("find . -mindepth 2 -name .git -type f -delete", self.script[checkout:])
    self.assertIn('git branch --unset-upstream "$TARGET_BRANCH"', self.script)

  def test_publication_is_authenticated_and_race_safe(self):
    self.assertIn('GIT_TERMINAL_PROMPT=0', self.script)
    self.assertIn('GIT_ASKPASS="$GIT_ASKPASS_FILE"', self.script)
    self.assertIn('https://github.com/', self.script)
    self.assertNotIn('GIT_SSH_COMMAND', self.script)
    self.assertIn('CURRENT_REMOTE" != "$EXPECTED_REMOTE', self.script)
    self.assertIn('--force-with-lease="$REMOTE_REF:$EXPECTED_REMOTE"', self.script)
    self.assertIn('git branch --set-upstream-to="$GIT_REMOTE/$TARGET_BRANCH"', self.script)

  def test_release_commit_records_source(self):
    self.assertIn('GIT_AUTHOR_DATE="$BUILD_DATE"', self.script)
    self.assertIn('-m "openpilot $TARGET_BRANCH prebuilt"', self.script)
    self.assertIn("date: $MESSAGE_DATE", self.script)
    self.assertIn("source: $SOURCE_BRANCH @ $SOURCE_COMMIT", self.script)
    self.assertIn('PREBUILT_TAG="prebuilts/$SOURCE_BRANCH/$SOURCE_COMMIT"', self.script)
    self.assertIn('git -C "$OUTPUT_DIR" init --quiet -b "$TARGET_BRANCH"', self.script)


if __name__ == "__main__":
  unittest.main()
