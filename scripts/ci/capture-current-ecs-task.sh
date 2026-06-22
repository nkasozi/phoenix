#!/usr/bin/env bash

set -euo pipefail

current_task_definition_arn="$(aws ecs describe-services \
  --cluster "$ECS_CLUSTER_NAME" \
  --services "$ECS_SERVICE_NAME" \
  --query 'services[0].taskDefinition' \
  --output text)"

echo "arn=$current_task_definition_arn" >> "$GITHUB_OUTPUT"
echo "[ecs] Current task definition: $current_task_definition_arn"
