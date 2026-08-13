# Comma-native prebuilt generation

The comma 4 records the source commit after its normal startup compilation.
Once that build has completed, the Developer panel's **Auto Prebuilt** action
packages the native binaries, or the same operation can be run over SSH:

```sh
cd /data/openpilot
release/create_mici_prebuilt.sh
```

With the provisioned deploy key at `/data/ssh/prebuilt-deploy-key`, this
publishes the generated commit to the target branch on `origin`. Override the
default key with `PREBUILT_GITHUB_SSH_KEY` or pass a different
GitHub-authorized private key:


```sh
release/create_mici_prebuilt.sh /path/to/github_private_key
```

The generated commit and its annotated tag use the persistent identity in
`/data/ssh/prebuilt-gitconfig`. This keeps their identity independent of
the installer-created checkout configuration. Provision it next to the deploy
key using Git's config format:

```sh
git config --file /data/ssh/prebuilt-gitconfig user.name sebzaduka
git config --file /data/ssh/prebuilt-gitconfig user.email \
  297784965+sebzaduka@users.noreply.github.com
chmod 600 /data/ssh/prebuilt-gitconfig
```

Override the identity-file path with `PREBUILT_GIT_IDENTITY`, or override its
values with both `PREBUILT_GIT_USER_NAME` and `PREBUILT_GIT_USER_EMAIL`. The
script fails before packaging when it cannot resolve both values; it never
falls back to the checkout's `user.name` or `user.email`.

If the default key is absent, no-argument invocation falls back to local-only
generation. Request that mode explicitly even when a deploy key is installed
with:

```sh
release/create_mici_prebuilt.sh --local-only
```

The source branch is inferred from the checkout. A name ending in `-src` maps
to the prebuilt branch with that suffix removed. Local-only mode performs no
GitHub operations. It creates an orphan prebuilt commit, checks it out, and leaves the branch without an upstream
because the commit has not been published. Activation uses the same forced,
non-recursive checkout behavior as the comma updater so initialized submodule
worktrees can be replaced by their flattened release contents. It then removes
residual nested Git metadata and other untracked, release-excluded files so the
activated target checkout contains no source submodule metadata and is clean.

Publishing verifies that the current clean HEAD exists on the GitHub origin.
It protects the target branch with force-with-lease, verifies the pushed
commit, then checks out the local target and configures it to track its origin
counterpart.
The key is applied only to this script's Git commands and is not saved in Git
or SSH configuration. Publishing also uses GitHub's pinned, officially
published Ed25519 host key from a temporary `known_hosts` file, so a fresh
AGNOS installation does not need persistent SSH host setup and an unexpected
GitHub host key still fails closed.

The script does not run SCons. It requires the build marker to match HEAD,
refuses to start while a build is running, and validates the expected ARM64
binaries and runtime libraries. While packaging, a volatile blocker prevents
the device from going on road. The Developer action reboots automatically;
direct invocation leaves the generated checkout ready for a manual reboot.

Every generated commit uses the xnor-tech prebuilt message format and receives
an annotated `prebuilts/<source-branch>/<source-sha>` tag. With the provisioned
credential, both the tag and derived prebuilt branch are published.

## Baseline updates

The packaged `openpilot/system/maintenance/baseline.json` identifies an old
baseline SHA and its branch/remote. When a newer branch tip is available, the
off-road notification or Developer action switches to the corresponding source
branch, rebases with `git rebase --onto NEW_BASELINE OLD_BASELINE`, publishes the
rewritten source and provenance tags, and runs Auto Prebuilt. A persistent
state file blocks on-road operation across the required source-branch reboot.
