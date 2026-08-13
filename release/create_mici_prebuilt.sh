#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_BRANCH="${PREBUILT_TARGET_BRANCH:-}"
SOURCE_BRANCH="${PREBUILT_SOURCE_BRANCH:-}"
GIT_REMOTE="${PREBUILT_GIT_REMOTE:-origin}"
WORK_PARENT="${PREBUILT_WORK_PARENT:-/data}"
LOCK_FILE="${PREBUILT_LOCK_FILE:-/tmp/openpilot-prebuilt-$UID.lock}"
DEFAULT_SSH_KEY="${PREBUILT_GITHUB_SSH_KEY:-/data/ssh/prebuilt-deploy-key}"
DEFAULT_GIT_IDENTITY="${PREBUILT_GIT_IDENTITY:-/data/ssh/prebuilt-gitconfig}"
WORK_DIR=""
SSH_KNOWN_HOSTS=""
BLOCKER_FILE="${PREBUILT_BLOCKER:-/tmp/openpilot-prebuilt.block}"

cleanup() {
  if test -n "$WORK_DIR"; then
    rm -rf -- "$WORK_DIR"
  fi
  if test -n "$SSH_KNOWN_HOSTS"; then
    rm -f -- "$SSH_KNOWN_HOSTS"
  fi
}
trap cleanup EXIT

usage() {
  echo "Usage: $0 [--local-only|GITHUB_SSH_PRIVATE_KEY]" >&2
  exit 2
}

if test "$#" -gt 1; then
  usage
fi

case "${1:-}" in
  --local-only) SSH_KEY="" ;;
  "")
    if test -f "$DEFAULT_SSH_KEY"; then
      SSH_KEY="$DEFAULT_SSH_KEY"
    else
      SSH_KEY=""
    fi
    ;;
  -*) usage ;;
  *) SSH_KEY="$1" ;;
esac
PUBLISH=0
if test -n "$SSH_KEY"; then
  PUBLISH=1
  SSH_KEY="$(realpath "$SSH_KEY")"
  if test ! -f "$SSH_KEY" || test ! -r "$SSH_KEY"; then
    echo "SSH private key is not a readable file: $SSH_KEY" >&2
    exit 1
  fi
  SSH_KNOWN_HOSTS="$(mktemp /tmp/github-known-hosts.XXXXXX)"
  printf '%s\n' \
    'github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl' \
    > "$SSH_KNOWN_HOSTS"
  chmod 600 "$SSH_KNOWN_HOSTS"
  printf -v GIT_SSH_COMMAND \
    'ssh -i %q -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=%q -o GlobalKnownHostsFile=/dev/null' \
    "$SSH_KEY" "$SSH_KNOWN_HOSTS"
  export GIT_SSH_COMMAND
fi

if test "$(uname -m)" != aarch64 || test ! -f /AGNOS || test ! -e /dev/ion; then
  echo "This script must run natively on an AGNOS comma 4" >&2
  exit 1
fi
if test "$ROOT" != /data/openpilot; then
  echo "This script must run from the /data/openpilot checkout" >&2
  exit 1
fi
if test "$(cat /data/params/d/IsOffroad 2>/dev/null || true)" != 1; then
  echo "This script may only run while the device is off road" >&2
  exit 1
fi
case "$WORK_PARENT" in
  /data|/data/*) ;;
  *) echo "PREBUILT_WORK_PARENT must be /data or below it" >&2; exit 1 ;;
esac
exec 9> "$LOCK_FILE"
if ! flock -n 9; then
  echo "Another prebuilt generation is already running" >&2
  exit 1
fi

cd "$ROOT"
SOURCE_COMMIT="$(git rev-parse HEAD)"
CURRENT_BRANCH="$(git branch --show-current)"
BUILD_MARKER="${OPENPILOT_BUILD_MARKER:-/tmp/openpilot-build.json}"
SOURCE_BRANCH="${SOURCE_BRANCH:-$CURRENT_BRANCH}"
if test -z "$TARGET_BRANCH" && [[ "$SOURCE_BRANCH" == *-src ]]; then
  TARGET_BRANCH="${SOURCE_BRANCH%-src}"
fi
if test -z "$TARGET_BRANCH"; then
  echo "A source branch ending in -src or PREBUILT_TARGET_BRANCH is required" >&2
  exit 1
fi
if test "$TARGET_BRANCH" = "$SOURCE_BRANCH"; then
  echo "Prebuilt target branch must differ from the source branch" >&2
  exit 1
fi
git check-ref-format --branch "$TARGET_BRANCH" >/dev/null
git check-ref-format --branch "$SOURCE_BRANCH" >/dev/null
if test "$CURRENT_BRANCH" != "$SOURCE_BRANCH"; then
  echo "Expected branch $SOURCE_BRANCH, currently on ${CURRENT_BRANCH:-detached HEAD}" >&2
  exit 1
fi
if test -e prebuilt; then
  echo "Current checkout is already a prebuilt" >&2
  exit 1
fi
if ! python3 -c 'import json, sys; raise SystemExit(0 if json.load(open(sys.argv[1]))["commit"] == sys.argv[2] else 1)' \
    "$BUILD_MARKER" "$SOURCE_COMMIT" 2>/dev/null; then
  echo "Current commit has not completed the normal device build" >&2
  exit 1
fi
if ! git for-each-ref --format='%(refname)' --contains "$SOURCE_COMMIT" refs/remotes/origin/ | grep -q .; then
  echo "Current HEAD is not present in an origin remote-tracking ref" >&2
  exit 1
fi
if test -n "$(git status --porcelain --untracked-files=no)"; then
  echo "Tracked files or submodules are dirty; refusing to package" >&2
  exit 1
fi

if git submodule status --recursive | grep -q '^-'; then
  echo "All recursive submodules must be initialized before packaging" >&2
  exit 1
fi
if pgrep -f '(^|/| )build\.py($| )|[s]cons' >/dev/null; then
  echo "The normal comma build is still running; wait for it to finish" >&2
  exit 1
fi

for binary in \
  openpilot/system/camerad/camerad \
  openpilot/system/loggerd/loggerd \
  openpilot/selfdrive/pandad/pandad; do
  if test ! -x "$binary"; then
    echo "Required build output is missing or not executable: $binary" >&2
    exit 1
  fi
  if ! file "$binary" | grep -q 'ARM aarch64'; then
    echo "Required build output is not ARM64: $binary" >&2
    exit 1
  fi
  LDD_OUTPUT="$(ldd "$binary" 2>&1)"
  if grep -q 'not found' <<< "$LDD_OUTPUT"; then
    echo "Required build output has unresolved libraries: $binary" >&2
    printf '%s\n' "$LDD_OUTPUT" >&2
    exit 1
  fi
done

if ! (set -o noclobber; : > "$BLOCKER_FILE") 2>/dev/null && test ! -f "$BLOCKER_FILE"; then
  echo "Unable to create on-road blocker: $BLOCKER_FILE" >&2
  exit 1
fi

REMOTE_REF="refs/heads/$TARGET_BRANCH"
EXPECTED_REMOTE=""
GIT_ORIGIN=""
if test "$PUBLISH" -eq 1; then
  GIT_ORIGIN="$(git remote get-url --push "$GIT_REMOTE")"
  if ! git ls-remote "$GIT_ORIGIN" | awk -v sha="$SOURCE_COMMIT" '$1 == sha { found=1 } END { exit !found }'; then
    echo "Current HEAD is not present on the published origin remote" >&2
    exit 1
  fi
  EXPECTED_REMOTE="$(git ls-remote --heads "$GIT_ORIGIN" "$REMOTE_REF" | awk '{print $1}')"
fi

GIT_USER_NAME="${PREBUILT_GIT_USER_NAME:-}"
GIT_USER_EMAIL="${PREBUILT_GIT_USER_EMAIL:-}"
if test -r "$DEFAULT_GIT_IDENTITY"; then
  GIT_USER_NAME="${GIT_USER_NAME:-$(git config --file "$DEFAULT_GIT_IDENTITY" user.name || true)}"
  GIT_USER_EMAIL="${GIT_USER_EMAIL:-$(git config --file "$DEFAULT_GIT_IDENTITY" user.email || true)}"
fi
if test -z "$GIT_USER_NAME" || test -z "$GIT_USER_EMAIL"; then
  echo "Prebuilt Git identity is missing from $DEFAULT_GIT_IDENTITY" >&2
  echo "Configure user.name and user.email there or set PREBUILT_GIT_USER_NAME and PREBUILT_GIT_USER_EMAIL" >&2
  exit 1
fi

WORK_DIR="$(mktemp -d "$WORK_PARENT/openpilot-prebuilt.XXXXXX")"
OUTPUT_DIR="$WORK_DIR/output"
FILE_LIST="$WORK_DIR/release-files"
mkdir "$OUTPUT_DIR"

{
  python3 tools/release/release_files.py
  # The normal source checkout build writes ignored runtime artifacts in place.
  # Include them before removing intermediate objects and caches below.
  git ls-files --others --ignored --exclude-standard -z
  git submodule foreach --recursive --quiet \
    'git ls-files --others --ignored --exclude-standard -z | sed -z "s#^#$displaypath/#"'
} | sort -zu > "$FILE_LIST"
rsync -aR --from0 --files-from="$FILE_LIST" ./ "$OUTPUT_DIR/"

find "$OUTPUT_DIR" -type f \( \
  -name '*.a' -o -name '*.gcda' -o -name '*.gcno' -o -name '*.o' -o \
  -name '*.os' -o -name '*.pyc' -o -name 'moc_*' -o \
  -name 'compile_commands.json' -o -name '.sconsign.dblite' \
  \) -delete
find "$OUTPUT_DIR" -type d \( \
  -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o \
  -name '*.egg-info' \
  \) -prune -exec rm -rf -- {} +
rm -rf -- \
  "$OUTPUT_DIR/.github" \
  "$OUTPUT_DIR/release" \
  "$OUTPUT_DIR/openpilot/selfdrive/ui/replay"
rm -f -- "$OUTPUT_DIR/Jenkinsfile" "$OUTPUT_DIR/SConstruct"
find "$OUTPUT_DIR" -name SConscript -type f -delete
find "$OUTPUT_DIR/openpilot/selfdrive/modeld/models" -maxdepth 1 -name '*.onnx*' -type f -delete 2>/dev/null || true
find "$OUTPUT_DIR/openpilot/sunnypilot" -path '*/modeld*/models/*.onnx*' -type f -delete 2>/dev/null || true
find "$OUTPUT_DIR/openpilot/third_party" -mindepth 1 -maxdepth 1 \( -name '*x86*' -o -name '*Darwin*' \) -exec rm -rf -- {} + 2>/dev/null || true
touch "$OUTPUT_DIR/prebuilt"

"$ROOT/release/validate_mici_prebuilt.sh" "$OUTPUT_DIR"
CONTAMINATION="$(find "$OUTPUT_DIR" -type f \( \
  -path '*/.pytest_cache/*' -o -path '*/.ruff_cache/*' -o \
  -name '*.gcda' -o -name '*.gcno' -o -name 'compile_commands.json' \
  \) -print -quit)"
if test -n "$CONTAMINATION"; then
  echo "Release contamination found: $CONTAMINATION" >&2
  exit 1
fi
OVERSIZED="$(find "$OUTPUT_DIR" -type f -size +100000000c -print -quit)"
if test -n "$OVERSIZED"; then
  echo "File exceeds GitHub's 100 MB limit: $OVERSIZED" >&2
  exit 1
fi

VERSION="$(awk -F\" '/SUNNYPILOT_VERSION/{print $2; exit}' "$OUTPUT_DIR/openpilot/sunnypilot/common/version.h")"
if test -z "$VERSION"; then
  echo "Unable to determine sunnypilot version" >&2
  exit 1
fi
BUILD_DATE="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
MESSAGE_DATE="${BUILD_DATE%%T*}"

git -C "$OUTPUT_DIR" init --quiet -b "$TARGET_BRANCH"
git -C "$OUTPUT_DIR" config user.name "$GIT_USER_NAME"
git -C "$OUTPUT_DIR" config user.email "$GIT_USER_EMAIL"
git -C "$OUTPUT_DIR" add -f .
GIT_AUTHOR_DATE="$BUILD_DATE" GIT_COMMITTER_DATE="$BUILD_DATE" \
  git -C "$OUTPUT_DIR" commit --quiet \
    -m "openpilot $TARGET_BRANCH prebuilt" \
    -m "date: $MESSAGE_DATE
source: $SOURCE_BRANCH @ $SOURCE_COMMIT"
RELEASE_COMMIT="$(git -C "$OUTPUT_DIR" rev-parse HEAD)"
PREBUILT_TAG="prebuilts/$SOURCE_BRANCH/$SOURCE_COMMIT"

# Import the commit before publishing so local checkout feasibility is independent
# of the GitHub connection after the potentially destructive branch update.
git fetch --quiet "$OUTPUT_DIR" "$RELEASE_COMMIT"
GIT_COMMITTER_NAME="$GIT_USER_NAME" GIT_COMMITTER_EMAIL="$GIT_USER_EMAIL" \
  git tag -fa "$PREBUILT_TAG" "$RELEASE_COMMIT" -m "$PREBUILT_TAG"
git branch -f "$TARGET_BRANCH" "$RELEASE_COMMIT"

if test "$PUBLISH" -eq 1; then
  git -C "$OUTPUT_DIR" remote add publish-origin "$GIT_ORIGIN"
  CURRENT_REMOTE="$(git -C "$OUTPUT_DIR" ls-remote --heads publish-origin "$REMOTE_REF" | awk '{print $1}')"
  if test "$CURRENT_REMOTE" != "$EXPECTED_REMOTE"; then
    echo "$TARGET_BRANCH changed while the prebuilt was being generated; refusing to publish" >&2
    exit 1
  fi
  git -C "$OUTPUT_DIR" push \
    --force-with-lease="$REMOTE_REF:$EXPECTED_REMOTE" \
    publish-origin "HEAD:$REMOTE_REF"
  git push --force "$GIT_ORIGIN" "refs/tags/$PREBUILT_TAG:refs/tags/$PREBUILT_TAG"
  PUBLISHED_REMOTE="$(git -C "$OUTPUT_DIR" ls-remote --heads publish-origin "$REMOTE_REF" | awk '{print $1}')"
  if test "$PUBLISHED_REMOTE" != "$RELEASE_COMMIT"; then
    echo "Remote branch verification failed" >&2
    exit 1
  fi
  PUBLISHED_TAG="$(git ls-remote "$GIT_ORIGIN" "refs/tags/$PREBUILT_TAG^{}" | awk '{print $1}')"
  if test "$PUBLISHED_TAG" != "$RELEASE_COMMIT"; then
    echo "Remote prebuilt tag verification failed" >&2
    exit 1
  fi
fi

# The source checkout contains initialized submodule worktrees and ignored model
# data. The release commit flattens those paths into ordinary tracked files, so
# match the updater's forced, non-recursive transition semantics.
git checkout --force --no-recurse-submodules -B "$TARGET_BRANCH" "$RELEASE_COMMIT"
# Nested repositories can retain their .git directories and release-excluded
# files after the forced transition. Remove all untracked residue exactly as
# the updater does after switching its overlay checkout.
git clean -xdff
# git clean deliberately preserves nested repository metadata even with two
# force flags. Release commits never contain .git entries, so remove pointer
# files left by initialized source submodules.
find . -mindepth 2 -name .git -type f -delete
if test "$PUBLISH" -eq 1; then
  git update-ref "refs/remotes/$GIT_REMOTE/$TARGET_BRANCH" "$RELEASE_COMMIT"
  git branch --set-upstream-to="$GIT_REMOTE/$TARGET_BRANCH" "$TARGET_BRANCH"
else
  git branch --unset-upstream "$TARGET_BRANCH" 2>/dev/null || true
fi

if test "$(git rev-parse HEAD)" != "$RELEASE_COMMIT" || test "$(git branch --show-current)" != "$TARGET_BRANCH"; then
  echo "Local prebuilt checkout verification failed" >&2
  exit 1
fi
sync
rm -f -- "$BLOCKER_FILE"

if test "$PUBLISH" -eq 1; then
  printf 'Published and checked out %s at %s\n' "$TARGET_BRANCH" "$RELEASE_COMMIT"
else
  printf 'Generated and checked out local-only %s at %s\n' "$TARGET_BRANCH" "$RELEASE_COMMIT"
fi
printf 'Source commit: %s\n' "$SOURCE_COMMIT"
printf 'Reboot the comma to activate the prebuilt.\n'
