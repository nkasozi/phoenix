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

print_failure_details() {
  echo "[ecs] Recent ECS service events:"
  "${describe_query_base[@]}" --query 'services[0].events[:10].[createdAt,message]' --output table || true
  print_failure_hints
  echo "[ecs] Final service snapshot:"
  "${describe_query_base[@]}" --query 'services[0].{status:status,desired:desiredCount,running:runningCount,pending:pendingCount,deployments:deployments[*].{status:status,rollout:rolloutState,reason:rolloutStateReason,desired:desiredCount,running:runningCount,pending:pendingCount,failed:failedTasks}}' --output json || true
}

echo "[ecs] Waiting for service stability: $ECS_SERVICE_NAME"
echo "[ecs] Timeout: ${timeout_seconds}s | Poll interval: ${poll_interval_seconds}s"

start_epoch="$(date +%s)"

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
