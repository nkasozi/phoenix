#!/usr/bin/env bash

set -euo pipefail

current_task_definition_arn="$(aws ecs describe-services \
  --cluster "$ECS_CLUSTER_NAME" \
  --services "$ECS_SERVICE_NAME" \
  --query 'services[0].taskDefinition' \
  --output text)"

if [[ -z "$current_task_definition_arn" || "$current_task_definition_arn" == "None" ]]; then
  echo "[ecs] ERROR - could not resolve a current task definition ARN for service '$ECS_SERVICE_NAME' in cluster '$ECS_CLUSTER_NAME'." >&2
  echo "[ecs] This usually means the service name is wrong or ECS has not registered a task definition yet." >&2
  exit 1
fi

echo "arn=$current_task_definition_arn" >> "$GITHUB_OUTPUT"
echo "[ecs] Current task definition: $current_task_definition_arn"
