#!/usr/bin/env bash

set -euo pipefail

image_tag="${GITHUB_SHA}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${GITHUB_JOB}"
echo "tag=$image_tag" >> "$GITHUB_OUTPUT"
echo "[image] Using immutable image tag: $image_tag"
