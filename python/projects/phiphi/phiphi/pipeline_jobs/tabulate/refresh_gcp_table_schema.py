"""Refresh the schema for the tabulated table.

It is recommended to run this script on a table that was created with the integration:
python/projects/phiphi/phiphi/tests/integration/test_bq_data_pipeline.py

You will need to have the test not delete the dataset at the end of the test to use this script.
See the test for how to do this.

Usage:
    python refresh_gcp_table_schema.py <table_id>
"""

import argparse
import os

from google.cloud import bigquery


def get_default_schema_path() -> str:
    """Get the default schema path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "tabulated_messages.schema.json")


def refresh_tabulate_schema(table_id: str, schema_path: str | None = None) -> None:
    """Refresh the schema for the tabulated table.

    Args:
        table_id (str): The table id.
        schema_path (str|None): The path to write the schema to.
            default: "tabulated_messages.schema.json" in the same directory as this script.
    """
    if table_id is None:
        raise ValueError("table_id is required.")

    if schema_path is None:
        schema_path = get_default_schema_path()

    client = bigquery.Client()
    table = client.get_table(table_id)  # Make an API request.

    # Write a schema file to schema_path with the schema_to_json method.
    client.schema_to_json(table.schema, schema_path)

    # View table properties
    print(f"Got table '{table.project}.{table.dataset_id}.{table.table_id}'.")
    print(f"Persisted schema to {schema_path}.")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Refresh the schema for the tabulated table.")
    parser.add_argument("table_id", type=str, help="The table id.")
    parser.add_argument("--schema_path", type=str, help="The path to write the schema to.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    refresh_tabulate_schema(args.table_id, args.schema_path)
