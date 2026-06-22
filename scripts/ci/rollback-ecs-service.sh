#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${TASK_DEFINITION_ARN:-}" || "${TASK_DEFINITION_ARN:-}" == "None" ]]; then
  echo "[ecs] SKIPPED - no known-good running task definition was available for rollback."
  echo "[ecs] The failed deployment remains visible for diagnosis instead of rolling back to an unverified bootstrap revision."
  exit 0
fi

echo "[ecs] Rolling back $ECS_SERVICE_NAME to $TASK_DEFINITION_ARN"
aws ecs update-service \
  --cluster "$ECS_CLUSTER_NAME" \
  --service "$ECS_SERVICE_NAME" \
  --task-definition "$TASK_DEFINITION_ARN"

ECS_STABILITY_TIMEOUT_SECONDS="${ECS_ROLLBACK_TIMEOUT_SECONDS:-900}" \
ECS_STABILITY_POLL_INTERVAL_SECONDS="${ECS_ROLLBACK_POLL_INTERVAL_SECONDS:-15}" \
bash scripts/ci/wait-for-ecs-service.sh

echo "[ecs] Rollback complete."
