"""Test the project init function."""

import pandas as pd
import pandas_gbq
import pytest
from google.cloud import bigquery

from phiphi import project_db
from phiphi.pipeline_jobs import constants, projects
from phiphi.pipeline_jobs.gathers import flow as gather_flow
from phiphi.tests.pipeline_jobs.gathers import example_gathers


def test_bq_project_init(tmp_project_namespace_with_cleanup):
    """Test project init function with a real Bigquery project."""
    tmp_project_namespace = tmp_project_namespace_with_cleanup
    projects.init_project_db.fn(tmp_project_namespace, "test", with_dummy_data=True)

    client = bigquery.Client()
    assert client.get_dataset(tmp_project_namespace)
    # Check that the dummy tabulated messages has been created
    assert client.get_table(f"{tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}")

    # Checking the schema autodetection of the hugging face external results table is working
    hugging_face_result_external_results = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.HF_FLOW_RESULTS_EXTERNAL_TABLE_NAME}"
    )
    assert len(hugging_face_result_external_results) > 0
    assert hugging_face_result_external_results.columns.tolist() == [
        "id",
        "label",
        "score",
        "job_run_id",
    ]

    # Check that will not fail if the dataset already exists.
    dataset = projects.init_project_db.fn(tmp_project_namespace, "test")
    assert client.get_dataset(dataset)

    projects.delete_project_db.fn(tmp_project_namespace)
    with pytest.raises(Exception):
        client.get_dataset(dataset)


@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "USE_MOCK_BQ": False,
    }
)
@pytest.mark.asyncio
async def test_bq_project_apply_migrations(
    patch_settings, tmp_project_namespace_with_cleanup, prefect_test_fixture
):
    """Test project apply migrations function with a real Bigquery project."""
    tmp_project_namespace = tmp_project_namespace_with_cleanup
    projects.init_project_db.fn(tmp_project_namespace, "test", with_dummy_data=True)

    client = bigquery.Client()
    assert client.get_dataset(tmp_project_namespace)
    # Check that the dummy tabulated messages has been created
    assert client.get_table(f"{tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}")

    tabulated_messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}"
    )

    assert len(tabulated_messages_df) > 0

    hf_scores = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.HF_FLOW_RESULTS_EXTERNAL_TABLE_NAME}"
    )

    assert len(hf_scores) > 0
    assert "job_run_id" in hf_scores.columns
    assert hf_scores["job_run_id"][0] == -1, "The seed data should have job_run_id -1"

    # Apply the migrations but nothing should happen as it should be up to date
    await projects.project_apply_migrations(
        job_run_id=1,
        project_id=1,
        project_namespace=tmp_project_namespace,
        active_classifiers_versions=[],
    )

    tabulated_messages_2_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}"
    )

    # The recompute should not have been run and the tabulate should be the same
    assert len(tabulated_messages_2_df) == len(tabulated_messages_df)
    pd.testing.assert_frame_equal(tabulated_messages_df, tabulated_messages_2_df)

    # Apply the migrations but nothing should happen as the alembic migration should be applied but
    # the recompute should not be applied due to no batches
    with project_db.init_connection(
        project_db.form_bigquery_sqlalchmey_uri(tmp_project_namespace)
    ) as connection:
        project_db.alembic_downgrade(connection, revision="-1")

    await projects.project_apply_migrations(
        job_run_id=1,
        project_id=1,
        project_namespace=tmp_project_namespace,
        active_classifiers_versions=[],
    )

    tabulated_messages_3_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}"
    )

    # The recompute should not have run because there are no batches (the data in tabulate was
    # dummy)
    assert len(tabulated_messages_3_df) == len(tabulated_messages_df)
    pd.testing.assert_frame_equal(tabulated_messages_df, tabulated_messages_3_df)

    # Apply the migrations after a gather_flow should recompute the tabulated messages and now have
    # the messages in the tabulated_messages.
    batch_size = 20
    gather_flow.gather_flow(
        gather_dict=example_gathers.facebook_posts_gather_example().dict(),
        gather_child_type=example_gathers.facebook_posts_gather_example().child_type,
        job_run_id=2,
        project_namespace=tmp_project_namespace,
        max_mb_batch_size=batch_size,
    )

    with project_db.init_connection(
        project_db.form_bigquery_sqlalchmey_uri(tmp_project_namespace)
    ) as connection:
        project_db.alembic_downgrade(connection, revision="-1")

    # Apply the migrations should not do the recompute as the recompute strategy is never
    await projects.project_apply_migrations(
        job_run_id=1,
        project_id=1,
        project_namespace=tmp_project_namespace,
        active_classifiers_versions=[],
        with_recompute_all_batches=projects.RecomputeStrategy.never,
    )

    tabulated_messages_4_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}"
    )

    assert len(tabulated_messages_4_df) == len(tabulated_messages_df)
    pd.testing.assert_frame_equal(tabulated_messages_df, tabulated_messages_4_df)

    with project_db.init_connection(
        project_db.form_bigquery_sqlalchmey_uri(tmp_project_namespace)
    ) as connection:
        project_db.alembic_downgrade(connection, revision="-1")

    # Apply migrations and recompute
    await projects.project_apply_migrations(
        job_run_id=1,
        project_id=1,
        project_namespace=tmp_project_namespace,
        active_classifiers_versions=[],
    )

    tabulated_messages_5_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}"
    )

    # The recompute should have been run and the table should contain the messages
    assert len(tabulated_messages_5_df) > len(tabulated_messages_df)
    assert len(tabulated_messages_5_df) == 8
    # Should not be equal because the data was updated
    assert not tabulated_messages_df.equals(tabulated_messages_5_df)
