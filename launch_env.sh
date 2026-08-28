#!/usr/bin/env bash

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

# models get lower priority than ui
# - ui is ~5ms
# - modeld is 20ms
# - DM is 10ms
# in order to run ui at 60fps (16.67ms), we need to allow
# it to preempt the model workloads. we have enough
# headroom for this until ui is moved to the CPU.
export QCOM_PRIORITY=12

# Apply an optional persistent AMD power limit before manager starts so every
# model runner inherits it. An explicit environment value takes precedence.
AM_POWER_LIMIT_FILE="${AM_POWER_LIMIT_FILE:-/data/am-power-limit}"
if test -z "${AM_POWER_LIMIT+x}" && test -r "$AM_POWER_LIMIT_FILE"; then
  AM_POWER_LIMIT="$(<"$AM_POWER_LIMIT_FILE")"
  if test -n "$AM_POWER_LIMIT"; then
    export AM_POWER_LIMIT
  fi
fi

if [ -z "$AGNOS_VERSION" ]; then
  export AGNOS_VERSION="19.6"
fi

export STAGING_ROOT="/data/safe_staging"
