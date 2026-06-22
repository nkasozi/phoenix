#!/usr/bin/env bash

set -euo pipefail

timeout_seconds="${ECS_STABILITY_TIMEOUT_SECONDS:-1200}"
poll_interval_seconds="${ECS_STABILITY_POLL_INTERVAL_SECONDS:-15}"

describe_query_base=(
  aws ecs describe-services
  --cluster "$ECS_CLUSTER_NAME"
  --services "$ECS_SERVICE_NAME"
)

echo "[ecs] Waiting for service stability: $ECS_SERVICE_NAME"
echo "[ecs] Timeout: ${timeout_seconds}s | Poll interval: ${poll_interval_seconds}s"

start_epoch="$(date +%s)"

while true; do
  now_epoch="$(date +%s)"
  elapsed="$((now_epoch - start_epoch))"

  status="$(${describe_query_base[@]} --query 'services[0].status' --output text)"
  desired="$(${describe_query_base[@]} --query 'services[0].desiredCount' --output text)"
  running="$(${describe_query_base[@]} --query 'services[0].runningCount' --output text)"
  pending="$(${describe_query_base[@]} --query 'services[0].pendingCount' --output text)"
  deployment_count="$(${describe_query_base[@]} --query 'length(services[0].deployments)' --output text)"
  primary_rollout="$(${describe_query_base[@]} --query "services[0].deployments[?status=='PRIMARY'].rolloutState | [0]" --output text)"

  echo "[ecs] elapsed=${elapsed}s status=${status} desired=${desired} running=${running} pending=${pending} deployments=${deployment_count} primary_rollout=${primary_rollout}"

  if [[ "$status" == "ACTIVE" ]] && [[ "$desired" == "$running" ]] && [[ "$pending" == "0" ]] && [[ "$deployment_count" == "1" ]] && [[ "$primary_rollout" == "COMPLETED" ]]; then
    echo "[ecs] OK - service is stable."
    exit 0
  fi

  if (( elapsed >= timeout_seconds )); then
    echo "[ecs] ERROR - timed out waiting for service stability after ${elapsed}s."
    echo "[ecs] Recent ECS service events:"
    ${describe_query_base[@]} --query 'services[0].events[:10].[createdAt,message]' --output table || true
    echo "[ecs] Final service snapshot:"
    ${describe_query_base[@]} --query 'services[0].{status:status,desired:desiredCount,running:runningCount,pending:pendingCount,deployments:deployments[*].{status:status,rollout:rolloutState,desired:desiredCount,running:runningCount,pending:pendingCount,failed:failedTasks}}' --output json || true
    exit 1
  fi

  # Show recent events periodically so deploy logs reveal why stabilization is delayed.
  if (( elapsed % 60 < poll_interval_seconds )); then
    echo "[ecs] Recent ECS service events:"
    ${describe_query_base[@]} --query 'services[0].events[:3].[createdAt,message]' --output table || true
  fi

  sleep "$poll_interval_seconds"
done
