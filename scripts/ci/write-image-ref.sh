#!/usr/bin/env bash

set -euo pipefail

image_ref="${ECR_REGISTRY}/${ECR_REPOSITORY}@${IMAGE_DIGEST}"
echo "image=$image_ref" >> "$GITHUB_OUTPUT"
echo "[image] Immutable image reference: $image_ref"
