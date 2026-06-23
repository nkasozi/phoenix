#!/usr/bin/env bash

set -euo pipefail

timeout_seconds="${ECS_STABILITY_TIMEOUT_SECONDS:-1200}"
poll_interval_seconds="${ECS_STABILITY_POLL_INTERVAL_SECONDS:-15}"

describe_query_base=(
  aws ecs describe-services
  --cluster "$ECS_CLUSTER_NAME"
  --services "$ECS_SERVICE_NAME"
)

print_failure_hints() {
  local recent_messages
  recent_messages="$("${describe_query_base[@]}" --query 'services[0].events[:20].message' --output text 2>/dev/null || true)"

  if echo "$recent_messages" | grep -qiE 'GetAuthorizationToken|cannot pull registry auth|ECR.*i/o timeout|api\.ecr\..*amazonaws\.com'; then
    echo "[ecs] DIAGNOSIS - Tasks cannot reach ECR to get auth token or pull image layers."
    echo "[ecs] ACTIONS - Verify ecr.api/ecr.dkr endpoints, S3 access, task outbound tcp/443, and NACL return traffic."
  fi
  if echo "$recent_messages" | grep -qiE 'unable to pull secrets|secretsmanager|ssm parameter'; then
    echo "[ecs] DIAGNOSIS - Task failed retrieving runtime secrets/parameters."
    echo "[ecs] ACTIONS - Verify execution-role permissions and access to Secrets Manager/SSM endpoints."
  fi
  if echo "$recent_messages" | grep -qiE 'CannotPullContainerError|pull image manifest has been retried'; then
    echo "[ecs] DIAGNOSIS - Image pull failed."
    echo "[ecs] ACTIONS - Verify the image, ECR policy, execution role, and network path."
  fi
  if echo "$recent_messages" | grep -qiE 'Health checks failed with these codes: \[404\]'; then
    echo "[ecs] DIAGNOSIS - The container is running, but the configured ALB health-check path returns HTTP 404."
    echo "[ecs] ACTIONS - Add the configured health route to the app or correct the infrastructure health-check path."
  fi
}

print_target_health() {
  local target_group_arn
  target_group_arn="$("${describe_query_base[@]}" --query 'services[0].loadBalancers[0].targetGroupArn' --output text 2>/dev/null || true)"
  if [[ -z "$target_group_arn" || "$target_group_arn" == "None" ]]; then
    echo "[ecs] No target group found on the service."
    return
  fi

  echo "[ecs] Target group health:"
  local target_health_output
  if ! target_health_output="$(aws elbv2 describe-target-health \
    --target-group-arn "$target_group_arn" \
    --query 'TargetHealthDescriptions[*].{target:Target.Id,port:Target.Port,state:TargetHealth.State,reason:TargetHealth.Reason,description:TargetHealth.Description}' \
    --output table 2>&1)"; then
    if echo "$target_health_output" | grep -q "AccessDenied"; then
      echo "[ecs] SKIPPED - target health unavailable; deploy role needs elasticloadbalancing:DescribeTargetHealth."
    else
      echo "[ecs] WARNING - target health lookup failed."
      echo "$target_health_output"
    fi
    return
  fi
  echo "$target_health_output"
}

print_recent_task_details() {
  local stopped_task_arns
  stopped_task_arns=($(aws ecs list-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --service-name "$ECS_SERVICE_NAME" \
    --desired-status STOPPED \
    --max-results 10 \
    --query 'taskArns' \
    --output text 2>/dev/null || true))

  if ((${#stopped_task_arns[@]} > 0)); then
    local stopped_task_ids=()
    for task_arn in "${stopped_task_arns[@]}"; do
      stopped_task_ids+=("${task_arn##*/}")
    done
    echo "[ecs] Recent stopped task details:"
    aws ecs describe-tasks \
      --cluster "$ECS_CLUSTER_NAME" \
      --tasks "${stopped_task_ids[@]}" \
      --query 'tasks[*].{task:taskArn,stoppedAt:stoppedAt,stopCode:stopCode,stoppedReason:stoppedReason,containers:containers[*].{name:name,lastStatus:lastStatus,exitCode:exitCode,reason:reason}}' \
      --output json || true
  else
    echo "[ecs] No stopped tasks found for this service."
  fi

  local active_task_arns
  active_task_arns=($(aws ecs list-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --service-name "$ECS_SERVICE_NAME" \
    --desired-status RUNNING \
    --max-results 10 \
    --query 'taskArns' \
    --output text 2>/dev/null || true))

  if ((${#active_task_arns[@]} > 0)); then
    local active_task_ids=()
    for task_arn in "${active_task_arns[@]}"; do
      active_task_ids+=("${task_arn##*/}")
    done
    echo "[ecs] Active task details:"
    aws ecs describe-tasks \
      --cluster "$ECS_CLUSTER_NAME" \
      --tasks "${active_task_ids[@]}" \
      --query 'tasks[*].{task:taskArn,lastStatus:lastStatus,healthStatus:healthStatus,containers:containers[*].{name:name,lastStatus:lastStatus,healthStatus:healthStatus,reason:reason}}' \
      --output json || true
  fi
}

print_task_definition_logging() {
  local task_definition_arn
  task_definition_arn="$("${describe_query_base[@]}" --query "services[0].deployments[?status=='PRIMARY'].taskDefinition | [0]" --output text 2>/dev/null || true)"
  if [[ -z "$task_definition_arn" || "$task_definition_arn" == "None" ]]; then
    echo "[ecs] No PRIMARY task definition found."
    return
  fi

  echo "[ecs] PRIMARY task definition logging config:"
  aws ecs describe-task-definition \
    --task-definition "$task_definition_arn" \
    --query 'taskDefinition.containerDefinitions[*].{name:name,logGroup:logConfiguration.options."awslogs-group",streamPrefix:logConfiguration.options."awslogs-stream-prefix"}' \
    --output table || true
}

print_recent_container_logs() {
  local task_definition_arn
  task_definition_arn="$("${describe_query_base[@]}" --query "services[0].deployments[?status=='PRIMARY'].taskDefinition | [0]" --output text 2>/dev/null || true)"
  if [[ -z "$task_definition_arn" || "$task_definition_arn" == "None" ]]; then
    return
  fi

  local log_groups
  log_groups=($(aws ecs describe-task-definition \
    --task-definition "$task_definition_arn" \
    --query 'taskDefinition.containerDefinitions[*].logConfiguration.options."awslogs-group"' \
    --output text 2>/dev/null || true))

  for log_group in "${log_groups[@]}"; do
    if [[ -z "$log_group" || "$log_group" == "None" ]]; then
      continue
    fi
    echo "[ecs] Recent CloudWatch logs from $log_group:"
    local log_streams
    log_streams=($(aws logs describe-log-streams \
      --log-group-name "$log_group" \
      --order-by LastEventTime \
      --descending \
      --max-items 2 \
      --query 'logStreams[*].logStreamName' \
      --output text 2>/dev/null || true))
    for log_stream in "${log_streams[@]}"; do
      echo "[ecs] Log stream: $log_stream"
      aws logs get-log-events \
        --log-group-name "$log_group" \
        --log-stream-name "$log_stream" \
        --limit 20 \
        --query 'events[*].[timestamp,message]' \
        --output table || true
    done
  done
}

collect_stopped_task_ids() {
  local stopped_task_arns
  stopped_task_arns=($(aws ecs list-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --service-name "$ECS_SERVICE_NAME" \
    --desired-status STOPPED \
    --max-results 10 \
    --query 'taskArns' \
    --output text 2>/dev/null || true))

  for task_arn in "${stopped_task_arns[@]}"; do
    echo "${task_arn##*/}"
  done
}

is_initial_stopped_task_id() {
  local candidate_task_id="$1"
  local initial_task_id
  for initial_task_id in "${initial_stopped_task_ids[@]}"; do
    if [[ "$candidate_task_id" == "$initial_task_id" ]]; then
      return 0
    fi
  done
  return 1
}

count_running_primary_tasks() {
  local primary_task_definition="$1"
  local active_task_arns
  active_task_arns=($(aws ecs list-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --service-name "$ECS_SERVICE_NAME" \
    --desired-status RUNNING \
    --max-results 10 \
    --query 'taskArns' \
    --output text 2>/dev/null || true))

  if ((${#active_task_arns[@]} == 0)); then
    echo 0
    return
  fi

  local active_task_ids=()
  local task_arn
  for task_arn in "${active_task_arns[@]}"; do
    active_task_ids+=("${task_arn##*/}")
  done

  aws ecs describe-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --tasks "${active_task_ids[@]}" \
    --output json 2>/dev/null \
    | jq -r --arg task_definition "$primary_task_definition" '[.tasks[]? | select(.taskDefinitionArn == $task_definition and .lastStatus == "RUNNING")] | length'
}

detect_new_primary_stopped_task_failure() {
  local primary_task_definition="$1"
  if [[ -z "$primary_task_definition" || "$primary_task_definition" == "None" ]]; then
    return 1
  fi

  local running_primary_count
  running_primary_count="$(count_running_primary_tasks "$primary_task_definition")"
  if [[ "$running_primary_count" =~ ^[0-9]+$ ]] && ((running_primary_count > 0)); then
    return 1
  fi

  local stopped_task_ids=()
  local task_id
  while IFS= read -r task_id; do
    if [[ -n "$task_id" ]] && ! is_initial_stopped_task_id "$task_id"; then
      stopped_task_ids+=("$task_id")
    fi
  done < <(collect_stopped_task_ids)

  if ((${#stopped_task_ids[@]} == 0)); then
    return 1
  fi

  aws ecs describe-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --tasks "${stopped_task_ids[@]}" \
    --output json 2>/dev/null \
    | jq -e --arg task_definition "$primary_task_definition" '
      any(.tasks[]?;
        .taskDefinitionArn == $task_definition
        and (
          .stopCode == "EssentialContainerExited"
          or any(.containers[]?; (.exitCode // 0) != 0)
        )
      )
    ' >/dev/null
}

print_failure_details() {
  echo "[ecs] Recent ECS service events:"
  "${describe_query_base[@]}" --query 'services[0].events[:10].[createdAt,message]' --output table || true
  print_failure_hints
  print_target_health
  print_recent_task_details
  print_task_definition_logging
  print_recent_container_logs
  echo "[ecs] Final service snapshot:"
  "${describe_query_base[@]}" --query 'services[0].{status:status,desired:desiredCount,running:runningCount,pending:pendingCount,deployments:deployments[*].{status:status,rollout:rolloutState,reason:rolloutStateReason,desired:desiredCount,running:runningCount,pending:pendingCount,failed:failedTasks}}' --output json || true
}

echo "[ecs] Waiting for service stability: $ECS_SERVICE_NAME"
echo "[ecs] Timeout: ${timeout_seconds}s | Poll interval: ${poll_interval_seconds}s"

start_epoch="$(date +%s)"
initial_stopped_task_ids=()
while IFS= read -r task_id; do
  if [[ -n "$task_id" ]]; then
    initial_stopped_task_ids+=("$task_id")
  fi
done < <(collect_stopped_task_ids)

while true; do
  now_epoch="$(date +%s)"
  elapsed="$((now_epoch - start_epoch))"

  status="$("${describe_query_base[@]}" --query 'services[0].status' --output text)"
  desired="$("${describe_query_base[@]}" --query 'services[0].desiredCount' --output text)"
  running="$("${describe_query_base[@]}" --query 'services[0].runningCount' --output text)"
  pending="$("${describe_query_base[@]}" --query 'services[0].pendingCount' --output text)"
  deployment_count="$("${describe_query_base[@]}" --query 'length(services[0].deployments)' --output text)"
  primary_rollout="$("${describe_query_base[@]}" --query "services[0].deployments[?status=='PRIMARY'].rolloutState | [0]" --output text)"
  primary_failed_tasks="$("${describe_query_base[@]}" --query "services[0].deployments[?status=='PRIMARY'].failedTasks | [0]" --output text)"
  primary_task_definition="$("${describe_query_base[@]}" --query "services[0].deployments[?status=='PRIMARY'].taskDefinition | [0]" --output text)"

  echo "[ecs] elapsed=${elapsed}s status=${status} desired=${desired} running=${running} pending=${pending} deployments=${deployment_count} primary_rollout=${primary_rollout} failed_tasks=${primary_failed_tasks}"

  if [[ "$status" == "ACTIVE" ]] && [[ "$desired" == "$running" ]] && [[ "$pending" == "0" ]] && [[ "$deployment_count" == "1" ]] && [[ "$primary_rollout" == "COMPLETED" ]]; then
    echo "[ecs] OK - service is stable."
    exit 0
  fi

  if [[ "$primary_rollout" == "FAILED" ]] || { [[ "$primary_failed_tasks" =~ ^[0-9]+$ ]] && (( primary_failed_tasks >= 3 )); }; then
    echo "[ecs] ERROR - deployment reached a terminal failure state; stopping the wait immediately."
    print_failure_details
    exit 1
  fi

  if detect_new_primary_stopped_task_failure "$primary_task_definition"; then
    echo "[ecs] ERROR - a new task for the current deployment stopped after an essential container failure; failing fast."
    print_failure_details
    exit 1
  fi

  if (( elapsed >= timeout_seconds )); then
    echo "[ecs] ERROR - timed out waiting for service stability after ${elapsed}s."
    print_failure_details
    exit 1
  fi

  if (( elapsed % 60 < poll_interval_seconds )); then
    echo "[ecs] Recent ECS service events:"
    "${describe_query_base[@]}" --query 'services[0].events[:3].[createdAt,message]' --output table || true
    print_failure_hints
  fi

  sleep "$poll_interval_seconds"
done
