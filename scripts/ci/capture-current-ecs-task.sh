#!/usr/bin/env bash

set -euo pipefail

running_task_arn="$(aws ecs list-tasks \
  --cluster "$ECS_CLUSTER_NAME" \
  --service-name "$ECS_SERVICE_NAME" \
  --desired-status RUNNING \
  --query 'taskArns[0]' \
  --output text)"

if [[ -z "$running_task_arn" || "$running_task_arn" == "None" ]]; then
  echo "arn=" >> "$GITHUB_OUTPUT"
  echo "[ecs] No running task exists, so there is no known-good rollback target."
  exit 0
fi

current_task_definition_arn="$(aws ecs describe-tasks \
  --cluster "$ECS_CLUSTER_NAME" \
  --tasks "$running_task_arn" \
  --query 'tasks[0].taskDefinitionArn' \
  --output text)"

if [[ -z "$current_task_definition_arn" || "$current_task_definition_arn" == "None" ]]; then
  echo "arn=" >> "$GITHUB_OUTPUT"
  echo "[ecs] No task definition could be resolved from the running task; rollback will be skipped."
  exit 0
fi

echo "arn=$current_task_definition_arn" >> "$GITHUB_OUTPUT"
echo "[ecs] Known-good running task definition: $current_task_definition_arn"
