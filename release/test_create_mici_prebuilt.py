#!/usr/bin/env python3
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestCommaPrebuiltContract(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.script = (ROOT / "release/create_mici_prebuilt.sh").read_text()

  def test_is_local_only(self):
    self.assertIn('Usage: $0 [--local-only]', self.script)
    self.assertIn('--local-only) ;;', self.script)
    self.assertNotIn("PREBUILT_GITHUB_TOKEN_FILE", self.script)
    self.assertNotIn("GIT_ASKPASS", self.script)
    self.assertNotIn("git ls-remote", self.script)
    self.assertNotIn('git -C "$OUTPUT_DIR" push', self.script)
    self.assertNotIn("publish-origin", self.script)

  def test_uses_persistent_local_commit_identity(self):
    self.assertIn('DEFAULT_GIT_IDENTITY="${PREBUILT_GIT_IDENTITY:-/data/prebuilt-publishing/gitconfig}"', self.script)
    self.assertIn('git config --file "$DEFAULT_GIT_IDENTITY" user.name', self.script)
    self.assertIn('git config --file "$DEFAULT_GIT_IDENTITY" user.email', self.script)
    self.assertIn('GIT_COMMITTER_NAME="$GIT_USER_NAME" GIT_COMMITTER_EMAIL="$GIT_USER_EMAIL"', self.script)

  def test_requires_native_completed_build(self):
    for contract in ('test "$(uname -m)" != aarch64', "test ! -f /AGNOS", "test ! -e /dev/ion", "pgrep -f"):
      self.assertIn(contract, self.script)
    self.assertIn('BUILD_MARKER="${OPENPILOT_BUILD_MARKER:-/tmp/openpilot-build.json}"', self.script)
    self.assertIn('m.get("artifact_policy") == "local-only"', self.script)
    self.assertIn('for t in ("small", "dm", "big")', self.script)
    self.assertIn("release/validate_mici_prebuilt.sh", self.script)
    self.assertIn('cat /data/params/d/IsOffroad', self.script)

  def test_always_requires_all_default_models(self):
    self.assertIn("MODEL_TARGETS=(small dm big)", self.script)
    self.assertIn('--validate --compatible --locally-built --targets "${MODEL_TARGETS[@]}"', self.script)
    self.assertNotIn("chestnut_present", self.script)
    self.assertNotIn("--require-big", self.script)

  def test_packages_ignored_runtime_build_outputs(self):
    self.assertIn("git ls-files --others --ignored --exclude-standard -z", self.script)
    self.assertIn("git submodule foreach --recursive --quiet", self.script)
    self.assertIn('sed -z "s#^#$displaypath/#"', self.script)
    self.assertIn("sort -zu", self.script)
    self.assertIn('rsync -aR --from0 --files-from="$FILE_LIST"', self.script)

  def test_generated_branch_is_local_and_clean(self):
    checkout_command = 'git checkout --force --no-recurse-submodules -B "$TARGET_BRANCH" "$RELEASE_COMMIT"'
    checkout = self.script.index(checkout_command)
    self.assertIn("git clean -xdff", self.script[checkout:])
    self.assertIn("find . -mindepth 2 -name .git -type f -delete", self.script[checkout:])
    self.assertIn('git branch --unset-upstream "$TARGET_BRANCH"', self.script[checkout:])
    self.assertIn("Generated and checked out local-only", self.script[checkout:])

  def test_release_commit_records_source_locally(self):
    self.assertIn('GIT_AUTHOR_DATE="$BUILD_DATE"', self.script)
    self.assertIn('-m "openpilot $TARGET_BRANCH prebuilt"', self.script)
    self.assertIn("date: $MESSAGE_DATE", self.script)
    self.assertIn("source: $SOURCE_BRANCH @ $SOURCE_COMMIT", self.script)
    self.assertIn('PREBUILT_TAG="prebuilts/$SOURCE_BRANCH/$SOURCE_COMMIT"', self.script)
    self.assertIn('git -C "$OUTPUT_DIR" init --quiet -b "$TARGET_BRANCH"', self.script)


if __name__ == "__main__":
  unittest.main()
