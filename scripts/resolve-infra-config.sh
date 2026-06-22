#!/usr/bin/env bash
# Resolve Phoenix infrastructure configuration directly from the Pulumi stack
# outputs at deploy time.
#
# The app repo only needs a single stable stack pointer and a Pulumi token:
#   - PHOENIX_PULUMI_STACK
#   - PULUMI_ACCESS_TOKEN
#
# Everything else is resolved live from `pulumi stack output`.

set -euo pipefail

log() { echo "[resolve] $*"; }
err() { echo "[resolve] ERROR: $*" >&2; }

if [[ -z "${PHOENIX_PULUMI_STACK:-}" ]]; then
  err "PHOENIX_PULUMI_STACK is not set. Set it to the fully-qualified Pulumi stack (org/project/stack)."
  exit 1
fi
if [[ -z "${PULUMI_ACCESS_TOKEN:-}" ]]; then
  err "PULUMI_ACCESS_TOKEN is not set. Add a read-scoped Pulumi Cloud token as a repository secret."
  exit 1
fi

GITHUB_OUTPUT="${GITHUB_OUTPUT:-/dev/stdout}"

if ! command -v pulumi >/dev/null 2>&1; then
  err "pulumi CLI not found on PATH. The workflow must install it before this step."
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  err "jq not found on PATH."
  exit 1
fi

log "Logging in to Pulumi Cloud (token-based, non-interactive)..."
pulumi login >/dev/null
log "OK    - logged in to Pulumi Cloud."

log "Reading stack outputs for '$PHOENIX_PULUMI_STACK'..."
pulumi_err="$(mktemp)"
if ! OUTPUTS="$(pulumi stack output --json --stack "$PHOENIX_PULUMI_STACK" 2>"$pulumi_err")"; then
  err "failed to read Pulumi stack outputs for '$PHOENIX_PULUMI_STACK':"
  cat "$pulumi_err" >&2
  rm -f "$pulumi_err"
  exit 1
fi
rm -f "$pulumi_err"

if [[ -z "$OUTPUTS" ]]; then
  err "no outputs returned for stack '$PHOENIX_PULUMI_STACK'. Is the stack deployed?"
  exit 1
fi

log "OK    - stack outputs loaded. Mapping to deploy inputs..."
log "source: ALL values below are read live from Pulumi stack '$PHOENIX_PULUMI_STACK' (not from GitHub vars/secrets)."

missing=0

emit() {
  local out_key="$1" json_key="$2" required="$3" value
  value="$(printf '%s' "$OUTPUTS" | jq -r --arg k "$json_key" '.[$k] // ""')"
  if [[ "$value" == "null" ]]; then
    value=""
  fi
  if [[ "$required" == "required" && -z "$value" ]]; then
    err "required Pulumi output '$json_key' is missing or empty in stack '$PHOENIX_PULUMI_STACK'."
    missing=1
    return
  fi
  printf '%s=%s\n' "$out_key" "$value" >> "$GITHUB_OUTPUT"
  if [[ -z "$value" ]]; then
    log "OK    - $out_key = <empty>            [source: Pulumi output '$json_key' (optional)]"
  else
    log "OK    - $out_key = '$value'  [source: Pulumi output '$json_key']"
  fi
}

emit deployment-mode     phoenixDeploymentMode       required
emit aws-region          awsRegion                    required
emit aws-role-to-assume  phoenixDeployGithubRoleArn  required
emit ecr-repository      phoenixRepositoryName       required
emit ecs-cluster-name    phoenixClusterName          required
emit ecs-service-name    phoenixServiceName          required
emit task-family         phoenixTaskFamily           required
emit api-ecr-repository phoenixApiRepositoryName    required
emit api-ecs-cluster-name phoenixApiClusterName     required
emit api-ecs-service-name phoenixApiServiceName     required
emit api-task-family    phoenixApiTaskFamily        required

load_balancer_dns_name="$(printf '%s' "$OUTPUTS" | jq -r '.phoenixLoadBalancerDnsName // empty')"
if [[ -z "$load_balancer_dns_name" ]]; then
  err "phoenixLoadBalancerDnsName is required to build the browser URL."
  missing=1
else
  printf 'app-url=http://%s\n' "$load_balancer_dns_name" >> "$GITHUB_OUTPUT"
  log "OK    - app-url = 'http://$load_balancer_dns_name' [derived from phoenixLoadBalancerDnsName]"
fi

api_load_balancer_dns_name="$(printf '%s' "$OUTPUTS" | jq -r '.phoenixApiLoadBalancerDnsName // empty')"
if [[ -z "$api_load_balancer_dns_name" ]]; then
  err "phoenixApiLoadBalancerDnsName is required to build the API URL."
  missing=1
else
  printf 'api-url=http://%s\n' "$api_load_balancer_dns_name" >> "$GITHUB_OUTPUT"
  log "OK    - api-url = 'http://$api_load_balancer_dns_name' [derived from phoenixApiLoadBalancerDnsName]"
fi

if [[ "$missing" -ne 0 ]]; then
  err "one or more required infrastructure outputs were missing. Aborting."
  exit 1
fi

log "OK    - all required infrastructure config resolved from Pulumi."
