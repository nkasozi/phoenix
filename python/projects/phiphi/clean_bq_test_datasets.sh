#!/bin/bash

# Description: Script to clean up all test datasets in BigQuery
# Usage: ./clean_bq_test_datasets.sh GCP_PROJECT_ID

# Check if GCP_PROJECT_ID is provided
if [ -z "$1" ]; then
  echo "Error: GCP_PROJECT_ID is required."
  echo "Usage: ./clean_bq_test_datasets.sh GCP_PROJECT_ID"
  exit 1
else
  GCP_PROJECT_ID=$1
fi

echo "Using GCP Project ID: $GCP_PROJECT_ID"

# List datasets, filter for 'test_' datasets, and remove them
bq ls --project_id="$GCP_PROJECT_ID" | \
grep -E ' test_' | \
awk '{print $1}' | \
xargs -I {} bq rm -r -f "${GCP_PROJECT_ID}:{}"
