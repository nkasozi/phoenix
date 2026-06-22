#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${TASK_DEFINITION_ARN:-}" || "${TASK_DEFINITION_ARN:-}" == "None" ]]; then
  echo "[ecs] SKIPPED - no previous task definition ARN was available for rollback."
  echo "[ecs] The deployment already failed, and there is no safe rollback target to apply."
  exit 0
fi

echo "[ecs] Rolling back $ECS_SERVICE_NAME to $TASK_DEFINITION_ARN"
aws ecs update-service \
  --cluster "$ECS_CLUSTER_NAME" \
  --service "$ECS_SERVICE_NAME" \
  --task-definition "$TASK_DEFINITION_ARN"
aws ecs wait services-stable \
  --cluster "$ECS_CLUSTER_NAME" \
  --services "$ECS_SERVICE_NAME"
echo "[ecs] Rollback complete."
