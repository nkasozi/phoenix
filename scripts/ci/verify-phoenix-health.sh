#!/usr/bin/env bash
# Verify the Phoenix public endpoints after deploy. This intentionally checks
# the browser-facing URL and the service health endpoint separately so the logs
# show whether we are failing at the front door or at the actual app health
# path.

set -euo pipefail

log() { echo "[health] $*"; }
err() { echo "[health] ERROR - $*" >&2; }

if [[ -z "${APP_URL:-}" ]]; then
  err "APP_URL is not set."
  exit 1
fi

root_url="${APP_URL%/}"
health_url="$root_url/health"

log "Public health checks"
log "Checking root URL: $root_url"
if curl -fsS --retry 8 --retry-delay 5 --max-time 15 "$root_url" >/dev/null; then
  log "OK - root URL is healthy."
else
  err "timed out or failed while checking root URL: $root_url"
  exit 1
fi

log "Checking health endpoint: $health_url"
if curl -fsS --retry 8 --retry-delay 5 --max-time 15 "$health_url" >/dev/null; then
  log "OK - health endpoint is healthy."
else
  err "timed out or failed while checking health endpoint: $health_url"
  exit 1
fi
