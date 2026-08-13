#!/usr/bin/env bash
set -euo pipefail

if test "$#" -gt 2 || test "$#" -lt 1; then
  echo "Usage: $0 PREBUILT_ROOT [--require-big]" >&2
  exit 2
fi

PREBUILT_ROOT="$1"
REQUIRE_BIG=0
if test "${2:-}" = "--require-big"; then
  REQUIRE_BIG=1
elif test "$#" -eq 2; then
  echo "Usage: $0 PREBUILT_ROOT [--require-big]" >&2
  exit 2
fi
CAMERAD="$PREBUILT_ROOT/openpilot/system/camerad/camerad"
for artifact in \
  openpilot/system/camerad/camerad \
  msgq_repo/msgq/ipc_pyx.so \
  msgq_repo/msgq/visionipc/visionipc_pyx.so \
  rednose_repo/rednose/helpers/ekf_sym_pyx.so; do
  if test ! -f "$PREBUILT_ROOT/$artifact"; then
    echo "required runtime artifact is missing: $artifact" >&2
    exit 1
  fi
done
test -x "$CAMERAD"

if ! file "$CAMERAD" | grep -q 'ARM aarch64'; then
  echo "comma 4 camerad is not an ARM64 executable: $CAMERAD" >&2
  exit 1
fi

STRINGS_FILE="$(mktemp /tmp/mici-camerad-strings.XXXXXX)"
trap 'rm -f "$STRINGS_FILE"' EXIT
strings "$CAMERAD" > "$STRINGS_FILE"

if ! grep -Fxq '/dev/ion' "$STRINGS_FILE"; then
  echo "comma 4 camerad does not contain the ION allocator" >&2
  exit 1
fi
if ! grep -Fq 'msgq/visionipc/visionbuf_ion.cc' "$STRINGS_FILE"; then
  echo "comma 4 camerad was not built from visionbuf_ion.cc" >&2
  exit 1
fi
if grep -Fq '/dev/shm/msgq_visionbuf_' "$STRINGS_FILE"; then
  echo "comma 4 camerad contains the generic shared-memory allocator" >&2
  exit 1
fi
if grep -Fq 'msgq/visionipc/visionbuf.cc' "$STRINGS_FILE"; then
  echo "comma 4 camerad contains visionbuf.cc" >&2
  exit 1
fi

MODEL_TARGETS=(small dm)
BIG_MANIFEST="$PREBUILT_ROOT/openpilot/selfdrive/modeld/models/big_driving_tinygrad.pkl.chunkmanifest"
if test "$REQUIRE_BIG" -eq 1 || test -f "$BIG_MANIFEST"; then
  MODEL_TARGETS+=(big)
fi
if ! PYTHONPATH="$PREBUILT_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    python3 "$PREBUILT_ROOT/openpilot/selfdrive/modeld/fetch_compiled_models.py" \
    --repo-root "$PREBUILT_ROOT" --destination "$PREBUILT_ROOT/openpilot/selfdrive/modeld/models" \
    --validate --targets "${MODEL_TARGETS[@]}"; then
  echo "compiled model artifact validation failed" >&2
  exit 1
fi

printf 'Validated comma 4 ION camerad: %s\n' "$CAMERAD"
