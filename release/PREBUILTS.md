# Comma-native prebuilt generation

The comma 4 records the source commit after its normal startup compilation.
Once that build has completed, the Developer panel's **Auto Prebuilt** action
packages the native binaries, or the same operation can be run over SSH:

```sh
cd /data/openpilot
release/create_mici_prebuilt.sh --local-only
```

Auto Prebuilt is strictly local. It never pushes the generated commit, branch,
tag, or model artifacts to GitHub. Passing `--local-only` remains supported to
make that policy explicit; invoking the script without an argument has the same
behavior.

The generated commit and its annotated tag use the persistent identity in
`/data/prebuilt-publishing/gitconfig`. This keeps their identity independent of
the installer-created checkout configuration. Provision it using Git's config
format:

```sh
git config --file /data/prebuilt-publishing/gitconfig user.name sebzaduka
git config --file /data/prebuilt-publishing/gitconfig user.email \
  297784965+sebzaduka@users.noreply.github.com
chmod 600 /data/prebuilt-publishing/gitconfig
```

Override the identity-file path with `PREBUILT_GIT_IDENTITY`, or override its
values with both `PREBUILT_GIT_USER_NAME` and `PREBUILT_GIT_USER_EMAIL`. The
script fails before packaging when it cannot resolve both values; it never
falls back to the checkout's `user.name` or `user.email`.

The source branch is inferred from the checkout. A name ending in `-src` maps
to the prebuilt branch with that suffix removed. Local-only mode performs no
GitHub operations. It creates an orphan prebuilt commit, checks it out, and
leaves the branch without an upstream. Activation uses the same forced,
non-recursive checkout behavior as the comma updater so initialized submodule
worktrees can be replaced by their flattened release contents. It then removes
residual nested Git metadata and other untracked, release-excluded files so the
activated target checkout contains no source submodule metadata and is clean.

The script does not run SCons. It requires the build marker to match HEAD,
refuses to start while a build is running, and validates the expected ARM64
binaries, runtime libraries, and locally built small, driver-monitoring, and
Chestnut big model artifacts. While packaging, a volatile blocker prevents the
device from going on road. The Developer action reboots automatically; direct
invocation leaves the generated checkout ready for a manual reboot.

Every generated commit uses the xnor-tech prebuilt message format and receives
an annotated local `prebuilts/<source-branch>/<source-sha>` tag.

## Default model artifacts

Normal AGNOS source builds compile the canonical small and driver-monitoring
models locally. When Chestnut is connected, SCons also compiles the repository's
default big model locally. Auto Prebuilt always requires compatible artifacts
for all three targets, even if Chestnut is disconnected by packaging time. A
source build completed without the big artifact remains usable as a source
checkout but is not eligible for Auto Prebuilt.

The stock big model is the repository's `big_driving_supercombo.onnx`, currently
named Lebowski, compiled to `big_driving_tinygrad.pkl`. A different big model
selected in sunnypilot is not compiled by this build. Its precompiled bundle is
downloaded separately into `/data/media/0/models` and run by `modeld_v2`. That
persistent selectable-model cache is independent and is not packaged or cleaned
by Auto Prebuilt.

## Baseline updates

The packaged `openpilot/system/maintenance/baseline.json` identifies an old
baseline SHA and its branch/remote. When a newer branch tip is available, the
off-road notification or Developer action switches to the corresponding source
branch, rebases with `git rebase --onto NEW_BASELINE OLD_BASELINE`, publishes the
rewritten source and provenance tags, and runs Auto Prebuilt. A persistent
state file blocks on-road operation across the required source-branch reboot.
The credential at `/data/prebuilt-publishing/github-token` is still used for
publishing these source-branch and provenance updates; it is never used by
local prebuilt generation.
