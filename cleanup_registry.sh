#!/bin/bash

# Script to delete all non-latest images from a local Docker registry

REGISTRY="http://localhost:32000"
REPOS=(
  "hugging-face-classifier-dev-image"
  "phiphi-dev-image"
  "phoenix_console"
  "phoenix_superset"
  "polarization-footprint-kenya-annotation"
  "privategather-api"
)

echo "Cleaning up non-latest images from $REGISTRY"
echo "============================================="

for repo in "${REPOS[@]}"; do
  echo ""
  echo "Processing: $repo"

  # Get all tags
  tags_response=$(curl -s "$REGISTRY/v2/$repo/tags/list")
  tags=$(echo "$tags_response" | jq -r '.tags[]?' 2>/dev/null)

  if [ -z "$tags" ]; then
    echo "  No tags found or error fetching tags"
    continue
  fi

  for tag in $tags; do
    if [ "$tag" == "latest" ]; then
      echo "  Keeping: $repo:$tag"
      continue
    fi

    if [ -n "$tag" ]; then
      echo "  Deleting: $repo:$tag"

      # Get digest
      digest=$(curl -s -I -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
        "$REGISTRY/v2/$repo/manifests/$tag" 2>&1 | grep -i "Docker-Content-Digest" | awk '{print $2}' | tr -d '\r')

      if [ -n "$digest" ]; then
        # Delete by digest
        response=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$REGISTRY/v2/$repo/manifests/$digest")
        if [ "$response" == "202" ]; then
          echo "    Success (digest: ${digest:0:30}...)"
        else
          echo "    Failed with HTTP $response (digest: ${digest:0:30}...)"
        fi
      else
        echo "    Failed to get digest"
      fi
    fi
  done
done

echo ""
echo "============================================="
echo "Cleanup complete."
echo ""
echo "To reclaim disk space, run garbage collection on your registry:"
echo "  docker exec <registry-container> bin/registry garbage-collect /etc/docker/registry/config.yml"
