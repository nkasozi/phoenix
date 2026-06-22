"""Test manual post authors classifier."""

import datetime

import pandas as pd
import pandas_gbq
import pytest

from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs.classify import flow as classify_flow


@pytest.mark.asyncio
async def test_manual_post_authors_classifier(tmp_bq_project):
    """Test the manual post authors classifier.

    This test that the data is uploaded correctly. The data pipeline will check that the tabulate
    works correctly.
    """
    test_project_namespace = tmp_bq_project
    classifier_id = 1
    version_id = 1
    job_run_id = 9

    # Step 1: Create the classifier dict
    classifier = {
        "id": classifier_id,
        "project_id": 10,
        "name": "test_manual_authors_classifier",
        "description": "Test manual authors classifier",
        "type": "manual_post_authors",
        "latest_version": {
            "version_id": version_id,
            "classifier_id": classifier_id,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "classes": [
                {"name": "spam_author", "description": "Authors who post spam"},
                {"name": "trusted_author", "description": "Trusted authors"},
            ],
            "params": {
                "author_classes": [
                    {
                        "class_name": "spam_author",
                        "phoenix_platform_message_author_id": "author_1",
                    },
                    {
                        "class_name": "trusted_author",
                        "phoenix_platform_message_author_id": "author_2",
                    },
                    {
                        "class_name": "trusted_author",
                        "phoenix_platform_message_author_id": "author_3",
                    },
                ]
            },
        },
    }

    # Step 2: Run the classifier for the first time
    await classify_flow.classify_flow(
        classifier_dict=classifier,
        project_namespace=test_project_namespace,
        job_run_id=job_run_id,
    )

    # Step 3: Check the classified authors table
    classified_authors_df = pandas_gbq.read_gbq(
        f"SELECT * "
        f"FROM {test_project_namespace}.{pipeline_jobs_constants.CLASSIFIED_AUTHORS_TABLE_NAME}"
    )

    expected_classified_authors_df = pd.DataFrame(
        {
            "classifier_id": pd.Series([classifier_id] * 3, dtype="Int64"),
            "classifier_version_id": pd.Series([version_id] * 3, dtype="Int64"),
            "class_name": ["spam_author", "trusted_author", "trusted_author"],
            "phoenix_platform_message_author_id": ["author_1", "author_2", "author_3"],
            "job_run_id": pd.Series([job_run_id] * 3, dtype="Int64"),
        }
    )

    pd.testing.assert_frame_equal(
        classified_authors_df.sort_index(axis=1)[expected_classified_authors_df.columns],
        expected_classified_authors_df.sort_index(axis=1),
        check_like=True,
    )

    # Step 4: Run the classifier again
    with pytest.raises(ValueError):
        await classify_flow.classify_flow(
            classifier_dict=classifier,
            project_namespace=test_project_namespace,
            job_run_id=job_run_id,
        )
