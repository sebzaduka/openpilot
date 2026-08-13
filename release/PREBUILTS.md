# Comma-native prebuilt generation

The comma 4 records the source commit after its normal startup compilation.
Once that build has completed, the Developer panel's **Auto Prebuilt** action
packages the native binaries, or the same operation can be run over SSH:

```sh
cd /data/openpilot
release/create_mici_prebuilt.sh
```

With the provisioned GitHub token at
`/data/prebuilt-publishing/github-token`, this publishes the generated commit
to the target branch on `origin`. Override the token-file path with
`PREBUILT_GITHUB_TOKEN_FILE`. The token is read by a temporary Git HTTPS
askpass helper and is never put in a remote URL, command argument, or Git
configuration.

## GitHub token permissions

Configure the permission when creating or editing the token in GitHub's user
settings:

1. Open **Profile picture → Settings → Developer settings → Personal access
   tokens → Fine-grained tokens**.
2. Select **Generate new token**, or select the existing token to edit it.
3. Set **Resource owner** to the user or organization that owns the repository
   configured as `origin`.
4. Under **Repository access**, select **Only select repositories**, then select
   that repository.
5. Under **Permissions → Repository permissions**, find **Contents** and select
   **Read and write**.
6. Generate or save the token.

GitHub also provides a
[pre-filled token form](https://github.com/settings/personal-access-tokens/new?contents=write&description=Publishes+comma-native+prebuilts&name=Prebuilt+publisher)
with **Contents: Read and write** selected. The resource owner and repository
still need to be selected manually.

GitHub also assigns **Metadata: Read-only** automatically. No other repository
or organization permissions are required. The account that creates the token
must have write access to the repository, and an organization-owned repository
may require an organization administrator to approve the token. Repository
rules and branch protection must also permit the account to force-update the
derived prebuilt branch and create or update the generated prebuilt tags.

See GitHub's documentation for
[creating a fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
and the [`Contents` repository permission](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens?apiVersion=2026-03-10#repository-permissions-for-contents).

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

If the token file is absent, no-argument invocation falls back to local-only
generation. Request that mode explicitly even when a token is installed
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
counterpart. Publishing uses the HTTPS GitHub remote, so it does not require
SSH credentials or `/data/ssh` state.

The script does not run SCons. It requires the build marker to match HEAD,
refuses to start while a build is running, and validates the expected ARM64
binaries and runtime libraries. While packaging, a volatile blocker prevents
the device from going on road. The Developer action reboots automatically;
direct invocation leaves the generated checkout ready for a manual reboot.

Every generated commit uses the xnor-tech prebuilt message format and receives
an annotated `prebuilts/<source-branch>/<source-sha>` tag. With the provisioned
credential, both the tag and derived prebuilt branch are published.

## Default model artifacts

Normal AGNOS source builds first look for exact compiled-model matches in
`sunnypilot/sunnypilot_models_v1` on Hugging Face. The ONNX content hash,
tinygrad gitlink, target class, backend, and chunk hashes must match. A cache
miss or network failure falls back to the existing local SCons compilation.
Auto Prebuilt validates the resulting small and driver-monitoring artifacts,
and also requires the Chestnut big artifact when Chestnut is connected. The
selectable model cache under `/data/media/0/models` is independent and is not
packaged or cleaned by this workflow.

## Baseline updates

The packaged `openpilot/system/maintenance/baseline.json` identifies an old
baseline SHA and its branch/remote. When a newer branch tip is available, the
off-road notification or Developer action switches to the corresponding source
branch, rebases with `git rebase --onto NEW_BASELINE OLD_BASELINE`, publishes the
rewritten source and provenance tags, and runs Auto Prebuilt. A persistent
state file blocks on-road operation across the required source-branch reboot.
