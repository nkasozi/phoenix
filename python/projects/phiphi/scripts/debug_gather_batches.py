r"""Debug script for gather batches that fail normalization.

This script retrieves gather batches from BigQuery and attempts to normalize each
item using the appropriate normalizer for the gather type. It identifies and reports
items that fail normalization, helping diagnose issues with gathered data.

Normalization can fail for several reasons:
- Apify scraping errors: The JSON blob contains an 'error' key
- Empty results: The JSON blob is missing the 'id' key (common for TikTok, Facebook, X)
- TikTok comments: 'noResults: true' or missing/empty user data
- Facebook search posts: Missing 'post_id' with 'message' key present
- Missing required fields: Platform-specific required fields are absent

Usage:
    From docker container:
        docker compose -f compose.yaml -f compose.dev.yaml exec api \
            python scripts/debug_gather_batches.py --project-id 133 --gather-id 1487

    From local python with GCP auth:
        python scripts/debug_gather_batches.py --project-id 133 --gather-id 1487

    Limit output per failed item:
        python scripts/debug_gather_batches.py -p 133 -g 1487 --max-chars 500

    Use a different GCP project:
        python scripts/debug_gather_batches.py -p 133 -g 1487 --gcp-project bu-phoenix-dev
"""

import argparse
import json

import pandas as pd
import pandas_gbq
from phiphi import utils
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs.gathers import normalise, normalisers


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Debug gather batches that fail normalization.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project-id 133 --gather-id 1487
  %(prog)s -p 133 -g 1487 --max-chars 500
  %(prog)s -p 133 -g 1487 --gcp-project bu-phoenix-dev
        """,
    )
    parser.add_argument(
        "-p",
        "--project-id",
        type=int,
        required=True,
        help="Phoenix project ID",
    )
    parser.add_argument(
        "-g",
        "--gather-id",
        type=int,
        required=True,
        help="Gather ID to debug",
    )
    parser.add_argument(
        "--gcp-project",
        type=str,
        default="bu-phoenix-prod",
        help="GCP project for BigQuery (default: bu-phoenix-prod)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=1000,
        help="Max characters to print per failed JSON blob (default: 1000)",
    )
    parser.add_argument(
        "--job-run-id",
        type=int,
        default=None,
        help="Optional: filter to a specific job run ID",
    )
    return parser.parse_args()


def print_failure(blob: dict, max_chars: int) -> None:
    """Print details about a failed normalization."""
    if normalisers.is_apify_scraping_error(blob):
        print(f"Apify error: {blob.get('error')}")
    elif normalisers.is_empty_result(blob):
        print("Empty result (no 'id' key)")
    else:
        print(f"Keys: {list(blob.keys())}")
        print(json.dumps(blob, indent=2, default=str)[:max_chars])


def process_batch(batch: pd.Series) -> tuple[int, list[tuple[int, dict]]]:
    """Process a single batch and return item count and failures."""
    batch_json = json.loads(batch["json_data"])
    gather_type = gathers_schemas.ChildTypeName(batch["gather_type"])
    normalizer = normalise.gather_normalisation_map[gather_type]

    failures = []
    for i, blob in enumerate(batch_json):
        result = normalizer(blob)
        if result is None:
            failures.append((i, blob))

    return len(batch_json), failures


def main() -> None:
    """Run the debug script."""
    args = parse_args()

    pandas_gbq.context.project = args.gcp_project

    dataset = utils.get_project_namespace(args.project_id)
    where_clause = f"gather_id = {args.gather_id}"
    if args.job_run_id:
        where_clause += f" AND job_run_id = {args.job_run_id}"

    query = f"""
    SELECT *
    FROM {dataset}.{constants.GATHER_BATCHES_TABLE_NAME}
    WHERE {where_clause}
    ORDER BY batch_id
    """

    print(f"Querying {args.gcp_project}:{dataset}.{constants.GATHER_BATCHES_TABLE_NAME}")
    print(f"Filter: {where_clause}\n")

    batches_df = pandas_gbq.read_gbq(query)

    if batches_df.empty:
        print("No batches found matching the criteria.")
        return

    print(f"Found {len(batches_df)} batches")
    print(batches_df[["gather_id", "job_run_id", "batch_id", "gather_type", "gathered_at"]])

    total_items = 0
    total_failures = 0

    for _, batch in batches_df.iterrows():
        item_count, failures = process_batch(batch)
        total_items += item_count
        total_failures += len(failures)

        if failures:
            batch_id = batch["batch_id"]
            print(f"\n=== Batch {batch_id}: {len(failures)}/{item_count} failures ===")
            for i, blob in failures:
                print(f"\n--- Item {i} ---")
                print_failure(blob, args.max_chars)

    print(f"\n{'=' * 60}")
    print(f"Summary: {total_failures}/{total_items} items failed normalization")
    if total_items > 0:
        success_rate = ((total_items - total_failures) / total_items) * 100
        print(f"Success rate: {success_rate:.1f}%")


if __name__ == "__main__":
    main()
