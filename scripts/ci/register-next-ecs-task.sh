#!/usr/bin/env bash

set -euo pipefail

aws ecs describe-task-definition \
  --task-definition "$TASK_FAMILY" \
  --query 'taskDefinition' \
  --output json > task-definition.json

jq \
  --arg container_name "$CONTAINER_NAME" \
  --arg image_uri "$IMAGE_REF" \
  '
    del(.compatibilities, .registeredAt, .registeredBy, .requiresAttributes, .revision, .status, .taskDefinitionArn)
    | .containerDefinitions = (.containerDefinitions | map(if .name == $container_name then .image = $image_uri else . end))
  ' task-definition.json > task-definition-next.json

next_task_definition_arn="$(aws ecs register-task-definition \
  --cli-input-json file://task-definition-next.json \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)"

echo "arn=$next_task_definition_arn" >> "$GITHUB_OUTPUT"
echo "[ecs] Registered next task definition: $next_task_definition_arn"
