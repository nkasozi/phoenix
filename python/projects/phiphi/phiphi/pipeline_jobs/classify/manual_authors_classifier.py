"""Manual authors classifier module.

This will be applied to manual_post_authors and other possible manual authors classifiers in the
future.
"""

import pandas as pd
import prefect

from phiphi.api.projects.classifiers.manual_post_authors import schemas
from phiphi.pipeline_jobs import classified_authors, utils


@prefect.task
def classify(
    classifier: schemas.ManualPostAuthorsClassifierPipeline, bigquery_dataset: str, job_run_id: int
) -> None:
    """Classify messages using manual authors classifier through BigQuery query."""
    # Retrieve the latest version details
    version = classifier.latest_version
    classifier_id = classifier.id
    classifier_version_id = version.version_id

    # Add a check that the classifier id and version id are not in classified_authors table
    table_name = classified_authors.constants.CLASSIFIED_AUTHORS_TABLE_NAME

    # Construct the query to check for existing entries
    query = f"""
        SELECT 1
        FROM `{bigquery_dataset}.{table_name}`
        WHERE classifier_id = {classifier_id}
          AND classifier_version_id = {classifier_version_id}
        LIMIT 1
    """

    # Read data using the utility function
    existing_entries_df = utils.read_data(query, bigquery_dataset, table_name)

    # If any entries are found, raise an error
    if not existing_entries_df.empty:
        raise ValueError(
            f"Classifier ID {classifier_id} with version ID {classifier_version_id} "
            "already exists in the classified_authors table. "
            "It is not possible to re-run a manual authors classifier with the same version ID "
            "as this could lead to unexpected behaviour. "
            "Please run again with a new version id."
        )

    # Proceed to classify and write data if no existing entries are found
    classified_authors_df = pd.DataFrame(version.params["author_classes"])
    classified_authors_df["classifier_id"] = classifier_id
    classified_authors_df["classifier_version_id"] = classifier_version_id
    classified_authors_df["job_run_id"] = job_run_id

    # Validate the DataFrame schema
    classified_authors.classified_authors_schema.validate(classified_authors_df)

    # Write the DataFrame to the BigQuery table
    utils.write_data(
        classified_authors_df,
        bigquery_dataset,
        table_name,
    )
