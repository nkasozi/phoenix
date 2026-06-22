#!/usr/bin/env bash

set -euo pipefail

echo "[ecs] Rolling back $ECS_SERVICE_NAME to $TASK_DEFINITION_ARN"
aws ecs update-service \
  --cluster "$ECS_CLUSTER_NAME" \
  --service "$ECS_SERVICE_NAME" \
  --task-definition "$TASK_DEFINITION_ARN"
aws ecs wait services-stable \
  --cluster "$ECS_CLUSTER_NAME" \
  --services "$ECS_SERVICE_NAME"
echo "[ecs] Rollback complete."
