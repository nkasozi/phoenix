#!/usr/bin/env bash

set -euo pipefail

if [[ -n "${ROLE_FROM_INPUT:-}" ]]; then
  echo "[auth] role-to-assume source: Pulumi stack output passed as workflow input."
elif [[ -n "${ROLE_FROM_VAR:-}" ]]; then
  echo "[auth] role-to-assume source: legacy GitHub variable AWS_ROLE_TO_ASSUME."
else
  echo "[auth] ERROR - no role to assume. Set the workflow input or AWS_ROLE_TO_ASSUME variable." >&2
  exit 1
fi
