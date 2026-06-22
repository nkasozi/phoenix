#!/usr/bin/env bash

set -euo pipefail

aws ecs update-service \
  --cluster "$ECS_CLUSTER_NAME" \
  --service "$ECS_SERVICE_NAME" \
  --task-definition "$TASK_DEFINITION_ARN"

echo "[ecs] Service update requested for $ECS_SERVICE_NAME."
