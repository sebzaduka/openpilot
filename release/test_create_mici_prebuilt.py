#!/usr/bin/env python3
import os
import pathlib
import subprocess
import tempfile
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
    self.assertIn('SOURCE_TRACKING_REF="refs/remotes/$GIT_REMOTE/$SOURCE_BRANCH"', self.script)
    self.assertIn('git rev-parse --verify "$SOURCE_TRACKING_REF"', self.script)
    self.assertIn('SOURCE_REMOTE_REF="refs/heads/$SOURCE_BRANCH"', self.script)
    self.assertIn('git ls-remote --heads "$GIT_ORIGIN" "$SOURCE_REMOTE_REF"', self.script)
    self.assertIn('PUBLISHED_SOURCE" != "$SOURCE_COMMIT', self.script)
    self.assertNotIn('git ls-remote "$GIT_ORIGIN" | awk', self.script)
    self.assertIn('remote set-url --push publish-origin "$GIT_ORIGIN"', self.script)
    self.assertIn('git -C "$OUTPUT_DIR" fetch --quiet "$ROOT"', self.script)
    self.assertIn('"+refs/tags/$PREBUILT_TAG:refs/tags/$PREBUILT_TAG"', self.script)
    self.assertIn('git -C "$OUTPUT_DIR" push --atomic', self.script)
    self.assertIn('--force-with-lease="$REMOTE_REF:$EXPECTED_REMOTE"', self.script)
    self.assertIn('"HEAD:$REMOTE_REF"', self.script)
    self.assertEqual(self.script.count('git -C "$OUTPUT_DIR" push'), 1)
    self.assertNotIn('git push --force "$GIT_ORIGIN"', self.script)
    self.assertNotIn('https://x-access-token:', self.script)
    self.assertIn('git branch --set-upstream-to="$GIT_REMOTE/$TARGET_BRANCH"', self.script)

  def test_explicit_pushurl_bypasses_global_push_instead_of(self):
    https_url = "https://github.com/example/repo.git"
    with tempfile.TemporaryDirectory() as temp_dir:
      temp = pathlib.Path(temp_dir)
      repo = temp / "repo"
      global_config = temp / "gitconfig"
      env = os.environ.copy()
      env.update({
        "GIT_CONFIG_GLOBAL": str(global_config),
        "GIT_CONFIG_SYSTEM": os.devnull,
        "HOME": str(temp),
      })

      subprocess.run(["git", "init", "--quiet", str(repo)], check=True, env=env)
      subprocess.run([
        "git", "config", "--file", str(global_config),
        "url.git@github.com:.pushInsteadOf", "https://github.com/",
      ], check=True, env=env)
      subprocess.run([
        "git", "-C", str(repo), "remote", "add", "publish-origin", https_url,
      ], check=True, env=env)

      get_push_url = ["git", "-C", str(repo), "remote", "get-url", "--push", "publish-origin"]
      rewritten = subprocess.run(get_push_url, check=True, env=env, text=True, capture_output=True).stdout.strip()
      self.assertEqual(rewritten, "git@github.com:example/repo.git")

      subprocess.run([
        "git", "-C", str(repo), "remote", "set-url", "--push", "publish-origin", https_url,
      ], check=True, env=env)
      explicit = subprocess.run(get_push_url, check=True, env=env, text=True, capture_output=True).stdout.strip()
      self.assertEqual(explicit, https_url)

  def test_tag_transfer_and_atomic_publication(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      temp = pathlib.Path(temp_dir)
      remote = temp / "remote.git"
      source = temp / "source"
      output = temp / "output"

      subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], check=True)
      for repo, branch in ((source, "source"), (output, "target")):
        subprocess.run(["git", "init", "--quiet", "-b", branch, str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", branch], check=True)

      subprocess.run(["git", "-C", str(source), "remote", "add", "origin", str(remote)], check=True)
      subprocess.run(["git", "-C", str(source), "push", "--quiet", "origin", "HEAD:refs/heads/target"], check=True)
      expected = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
      release = subprocess.check_output(["git", "-C", str(output), "rev-parse", "HEAD"], text=True).strip()
      tag = "refs/tags/prebuilts/source/initial"

      subprocess.run(["git", "-C", str(source), "fetch", "--quiet", str(output), release], check=True)
      subprocess.run(["git", "-C", str(source), "tag", "-fa", tag.removeprefix("refs/tags/"), release,
                      "-m", tag.removeprefix("refs/tags/")], check=True)
      subprocess.run(["git", "-C", str(output), "fetch", "--quiet", str(source), f"+{tag}:{tag}"], check=True)
      transferred = subprocess.check_output(["git", "-C", str(output), "rev-parse", f"{tag}^{{}}"], text=True).strip()
      self.assertEqual(transferred, release)

      subprocess.run(["git", "-C", str(output), "remote", "add", "publish-origin", str(remote)], check=True)
      subprocess.run([
        "git", "-C", str(output), "push", "--quiet", "--atomic",
        f"--force-with-lease=refs/heads/target:{expected}", "publish-origin",
        "HEAD:refs/heads/target", f"+{tag}:{tag}",
      ], check=True)
      self.assertEqual(subprocess.check_output(["git", f"--git-dir={remote}", "rev-parse", "refs/heads/target"],
                                               text=True).strip(), release)
      self.assertEqual(subprocess.check_output(["git", f"--git-dir={remote}", "rev-parse", f"{tag}^{{}}"],
                                               text=True).strip(), release)

      subprocess.run(["git", "-C", str(output), "commit", "--quiet", "--allow-empty", "-m", "retry"], check=True)
      retry = subprocess.check_output(["git", "-C", str(output), "rev-parse", "HEAD"], text=True).strip()
      retry_tag = "refs/tags/prebuilts/source/retry"
      subprocess.run(["git", "-C", str(output), "tag", "-a", retry_tag.removeprefix("refs/tags/"),
                      "-m", retry_tag.removeprefix("refs/tags/")], check=True)
      subprocess.run(["git", "-C", str(source), "commit", "--quiet", "--allow-empty", "-m", "concurrent"], check=True)
      concurrent = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
      subprocess.run(["git", "-C", str(source), "push", "--quiet", "--force", "origin", "HEAD:refs/heads/target"],
                     check=True)
      rejected = subprocess.run([
        "git", "-C", str(output), "push", "--quiet", "--atomic",
        f"--force-with-lease=refs/heads/target:{release}", "publish-origin",
        "HEAD:refs/heads/target", f"+{retry_tag}:{retry_tag}",
      ], capture_output=True)
      self.assertNotEqual(rejected.returncode, 0)
      self.assertEqual(subprocess.check_output(["git", f"--git-dir={remote}", "rev-parse", "refs/heads/target"],
                                               text=True).strip(), concurrent)
      self.assertNotEqual(concurrent, retry)
      missing_tag = subprocess.run(["git", f"--git-dir={remote}", "rev-parse", "--verify", retry_tag],
                                   capture_output=True)
      self.assertNotEqual(missing_tag.returncode, 0)

  def test_release_commit_records_source(self):
    self.assertIn('GIT_AUTHOR_DATE="$BUILD_DATE"', self.script)
    self.assertIn('-m "openpilot $TARGET_BRANCH prebuilt"', self.script)
    self.assertIn("date: $MESSAGE_DATE", self.script)
    self.assertIn("source: $SOURCE_BRANCH @ $SOURCE_COMMIT", self.script)
    self.assertIn('PREBUILT_TAG="prebuilts/$SOURCE_BRANCH/$SOURCE_COMMIT"', self.script)
    self.assertIn('git -C "$OUTPUT_DIR" init --quiet -b "$TARGET_BRANCH"', self.script)


if __name__ == "__main__":
  unittest.main()
