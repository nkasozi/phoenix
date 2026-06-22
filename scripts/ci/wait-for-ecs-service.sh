#!/usr/bin/env bash

set -euo pipefail

echo "[ecs] Waiting for service stability: $ECS_SERVICE_NAME"
aws ecs wait services-stable \
  --cluster "$ECS_CLUSTER_NAME" \
  --services "$ECS_SERVICE_NAME"
echo "[ecs] OK - service is stable."
