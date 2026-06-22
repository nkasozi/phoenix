"""Integration tests for the data pipeline with big query.

Instructions on running these tests without having to setup the local platform database:
- In `phiphi/config.py`:
   - Set `USE_MOCK_APIFY: bool = True`
   - Add `None` default to `SQLALCHEMY_DATABASE_URI: ... | None = None`
- In `python/projects/phiphi/docker_env.dev` set `USE_MOCK_BQ` to False.
- Login to Prefect cloud via CLI using API key from `Phoenix Dev` (buildup+dev@datavaluepeople.com)
  workspace
- Delete everything in `tests/confest.py`
- Set env var `export GOOGLE_CLOUD_PROJECT="bu-phoenix-dev"`
- Run `make test_integration` to run the tests

To not delete the resultant tables in BQ for inspection you need to alter the pytest fixture
`tmp_bq_project`.
"""

import asyncio
import datetime
from unittest.mock import patch

import pandas as pd
import pandas_gbq
import pytest

from phiphi import config
from phiphi.pipeline_jobs import constants, generalised_authors
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils
from phiphi.pipeline_jobs.classify import flow as classify_flow
from phiphi.pipeline_jobs.composite_flows import (
    delete_gather_tabulate_flow,
    recompute_all_batches_tabulate_flow,
)
from phiphi.pipeline_jobs.gathers import flow as gather_flow
from phiphi.pipeline_jobs.gathers import normalisers, selectors
from phiphi.pipeline_jobs.gathers import types as gather_types
from phiphi.pipeline_jobs.tabulate import flow as tabulate_flow
from phiphi.tests.pipeline_jobs.gathers import example_gathers

PHOENIX_AUTHOR_ID_FACEBOOK_POSTER = "c36c0135-7179-25f2-08b4-30fb2f96ff04"


def assert_tabulated_messages_are_equal(
    tabulated_messages_df: pd.DataFrame, tabulated_messages_after_recompute_df: pd.DataFrame
):
    """Assert that the tabulated messages are equal."""
    assert len(tabulated_messages_after_recompute_df) == len(tabulated_messages_df)
    columns_to_compare = ["post_id", "comment_id"]
    df_1 = tabulated_messages_df.sort_values(by=columns_to_compare).reset_index(drop=True)
    df_1 = df_1[columns_to_compare]
    df_2 = tabulated_messages_after_recompute_df.sort_values(by=columns_to_compare).reset_index(
        drop=True
    )
    df_2 = df_2[columns_to_compare]

    pd.testing.assert_frame_equal(df_1, df_2)


def test_bq_pipeline_integration(tmp_bq_project):
    """Test pipeline integration with bigquery.

    WARNING: !!!!!!!!!!!!!!
    The patch settings fixture/monkey patching env vars does not work with Prefect flows.

    This test creates a Bigquery dataset with name `test_<random_prefix>`.

    Then runs a gather flow using sample example data (no Apify calls, unless you override the
    projects settings to disable using Mock apify).

    It then checks a number of other flows and pipeline processes.

    Finally, it deletes the dataset.

    If the test fails you may need to manually clean up (delete) the dataset within Bigquery.
    """
    if config.settings.USE_MOCK_BQ:
        raise Exception(
            "This test requires USE_MOCK_BQ to be set to False. "
            "Please change this in python/projects/phiphi/docker_env.dev."
        )

    test_project_namespace = tmp_bq_project

    batch_size = 20
    batch_of_batches_size = 2

    with patch("phiphi.pipeline_jobs.gathers.utils.load_sample_raw_data", return_value=[]):
        pipeline_result = gather_flow.gather_flow(
            gather_dict=example_gathers.facebook_posts_gather_example().dict(),
            gather_child_type=example_gathers.facebook_posts_gather_example().child_type,
            job_run_id=1,
            project_namespace=test_project_namespace,
            max_mb_batch_size=batch_size,
            batch_of_batches_size=batch_of_batches_size,
        )
    assert pipeline_result is not None
    assert pipeline_result.cost == 0.0
    assert pipeline_result.result_count == 0

    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    assert messages_df.shape[0] == 0

    # Check that the get total count post authors returns 0 if no table
    total_post_authors = generalised_authors.get_total_count_post_authors(
        project_namespace=test_project_namespace
    )
    assert total_post_authors == 0

    # Check that the tabulate can run after a scrape with 0
    tabulate_flow.tabulate_flow(
        job_run_id=1, project_namespace=test_project_namespace, active_classifiers_versions=[]
    )

    # Using patch_settings and mocking APIFY_API_KEYS does not work here
    # You need to set this in the environment

    scrape_cost = gather_types.ScrapeCost(
        cost=5.0,
        is_cost_estimated=False,
    )
    with patch("phiphi.pipeline_jobs.gathers.apify.scrape.MOCK_APIFY_SCRAPE_COST", scrape_cost):
        pipeline_result = gather_flow.gather_flow(
            gather_dict=example_gathers.facebook_posts_gather_example().dict(),
            gather_child_type=example_gathers.facebook_posts_gather_example().child_type,
            job_run_id=1,
            project_namespace=test_project_namespace,
            max_mb_batch_size=batch_size,
            batch_of_batches_size=batch_of_batches_size,
        )
    assert pipeline_result is not None
    assert pipeline_result.cost == scrape_cost.cost
    # There is one error that is skipped in the normalisation
    assert pipeline_result.result_count == 9

    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    assert len(messages_df) == 8

    gather_flow.gather_flow(
        gather_dict=example_gathers.facebook_posts_gather_example().dict(),
        gather_child_type=example_gathers.facebook_posts_gather_example().child_type,
        job_run_id=2,
        project_namespace=test_project_namespace,
        max_mb_batch_size=batch_size,
        batch_of_batches_size=batch_of_batches_size,
    )

    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    assert len(messages_df) == 16
    deduped_messages_df = pandas_gbq.read_gbq(
        f"""
       SELECT *
       FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}
       """
    )
    assert len(deduped_messages_df) == 8

    deduped_authors_df = pandas_gbq.read_gbq(
        f"""
       SELECT *
       FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_AUTHORS_TABLE_NAME}
       """
    )
    assert len(deduped_authors_df) == 2

    post_authors_df = generalised_authors.get_post_authors(
        project_namespace=test_project_namespace
    )
    assert len(post_authors_df) == 2

    post_authors_df = generalised_authors.get_post_authors(
        project_namespace=test_project_namespace,
        offset=1,
        limit=1,
    )
    assert len(post_authors_df) == 1
    # Should be the second author that was gotten
    assert post_authors_df.iloc[0]["post_count"] == 4
    assert post_authors_df.iloc[0]["comment_count"] == 0

    facebook_author = generalised_authors.get_author(
        project_namespace=test_project_namespace,
        phoenix_platform_message_author_id=PHOENIX_AUTHOR_ID_FACEBOOK_POSTER,
    )
    assert facebook_author is not None
    assert (
        facebook_author["phoenix_platform_message_author_id"] == PHOENIX_AUTHOR_ID_FACEBOOK_POSTER
    )

    # Check that the get author returns None if not found
    facebook_author = generalised_authors.get_author(
        project_namespace=test_project_namespace, phoenix_platform_message_author_id="not_found"
    )
    assert facebook_author is None

    gather_flow.gather_flow(
        gather_dict=example_gathers.facebook_comments_gather_example().dict(),
        gather_child_type=example_gathers.facebook_comments_gather_example().child_type,
        job_run_id=3,
        project_namespace=test_project_namespace,
        max_mb_batch_size=batch_size,
        batch_of_batches_size=batch_of_batches_size,
    )

    batches_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GATHER_BATCHES_TABLE_NAME}"
    )
    assert len(batches_df) == 3
    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    assert len(messages_df) == 25
    deduped_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}
        """
    )
    assert len(deduped_messages_df) == 17
    deduped_authors_df = pandas_gbq.read_gbq(
        f"""
       SELECT *
       FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_AUTHORS_TABLE_NAME}
       ORDER BY post_count DESC, comment_count DESC
       """
    )
    assert len(deduped_authors_df) == 10
    assert deduped_authors_df.iloc[0]["post_count"] == 4
    assert deduped_authors_df.iloc[0]["comment_count"] == 1
    assert deduped_authors_df.iloc[2]["post_count"] == 0

    # Still only authors with posts
    post_authors_df = generalised_authors.get_post_authors(
        project_namespace=test_project_namespace
    )
    assert len(post_authors_df) == 2

    total_post_authors = generalised_authors.get_total_count_post_authors(
        project_namespace=test_project_namespace
    )
    assert total_post_authors == 2

    tabulate_flow.tabulate_flow(
        job_run_id=4, project_namespace=test_project_namespace, active_classifiers_versions=[]
    )

    tabulated_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}
        """
    )
    # There is 1 comment without a post
    assert len(tabulated_messages_df) == 15
    # Test that "class"/"comment_class" columns exists in the tabulated messages and has NaN values
    assert tabulated_messages_df["post_class"].isna().all()
    assert tabulated_messages_df["comment_class"].isna().all()
    assert tabulated_messages_df["phoenix_job_run_id"].unique() == [4]

    tabulated_post_post_messages_df = pandas_gbq.read_gbq(
        f"""
           SELECT *
           FROM {test_project_namespace}.{constants.POST_POST_CLASS_CONNECTION_TABLE_NAME}
           """
    )
    assert len(tabulated_post_post_messages_df) == 8
    # Test that "post_class"/"post_class_2" columns exists in the tabulated messages and has NaN
    # values
    assert tabulated_post_post_messages_df["post_class"].isna().all()
    assert tabulated_post_post_messages_df["post_class_2"].isna().all()

    tabulated_comment_comment_messages_df = pandas_gbq.read_gbq(
        f"""
           SELECT *
           FROM {test_project_namespace}.{constants.COMMENT_COMMENT_CLASS_CONNECTION_TABLE_NAME}
           """
    )
    assert len(tabulated_comment_comment_messages_df) == 10
    # Test that "comment_class"/"comment_class_2" columns exists in the tabulated messages and has
    # NaN values
    assert tabulated_comment_comment_messages_df["comment_class"].isna().all()
    assert tabulated_comment_comment_messages_df["comment_class_2"].isna().all()

    ## Recompute all batches and tabulate flow

    recompute_all_batches_tabulate_flow.recompute_all_batches_tabulate_flow(
        job_run_id=10,
        project_id=1,
        project_namespace=test_project_namespace,
        active_classifiers_versions=[],
    )

    messages_after_recompute_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    duplicated_messages = pd.concat([messages_df, messages_df], ignore_index=True)
    assert len(messages_after_recompute_df) == len(duplicated_messages)
    deduped_authors_after_recompute_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_AUTHORS_TABLE_NAME}
        ORDER BY post_count DESC
        """
    )
    assert len(deduped_authors_after_recompute_df) == len(deduped_authors_df)

    # Due to the ordering of the data not being consistent we do group by the message ID
    # and check that the counts are the same.
    grouped_messages = duplicated_messages.groupby("phoenix_platform_message_id").count()
    grouped_messages_after_recompute = messages_after_recompute_df.groupby(
        "phoenix_platform_message_id"
    ).count()
    pd.testing.assert_frame_equal(grouped_messages, grouped_messages_after_recompute)

    tabulated_messages_after_recompute_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}
        """
    )
    assert_tabulated_messages_are_equal(
        tabulated_messages_df, tabulated_messages_after_recompute_df
    )
    # Check that the processed_at is greater than the previous processed_at
    previous_processed_at = tabulated_messages_df["phoenix_processed_at"].max()
    recompute_processed_at = tabulated_messages_after_recompute_df["phoenix_processed_at"].unique()
    # Make sure that all the processed_at values are the same
    assert recompute_processed_at.shape[0] == 1
    # Make sure that the recompute processed_at is greater than the previous processed_at
    assert recompute_processed_at[0] > previous_processed_at
    assert tabulated_messages_after_recompute_df["phoenix_job_run_id"].unique() == [10]

    # Recompute just 1 gathers
    recompute_all_batches_tabulate_flow.recompute_all_batches_tabulate_flow(
        job_run_id=10,
        project_id=1,
        project_namespace=test_project_namespace,
        active_classifiers_versions=[],
        gather_ids=[example_gathers.facebook_posts_gather_example().id],
    )

    messages_after_recompute_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    # 16 is the number of messages in facebook_posts_gather_example
    assert len(messages_after_recompute_df) == len(duplicated_messages) + 16

    # Recompute with a drop
    recompute_all_batches_tabulate_flow.recompute_all_batches_tabulate_flow(
        job_run_id=11,
        project_id=1,
        project_namespace=test_project_namespace,
        active_classifiers_versions=[],
        drop_downstream_tables=True,
    )

    messages_after_recompute_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    assert len(messages_after_recompute_df) == len(messages_df)
    grouped_messages = messages_df.groupby("phoenix_platform_message_id").count()
    grouped_messages_after_recompute = messages_after_recompute_df.groupby(
        "phoenix_platform_message_id"
    ).count()
    pd.testing.assert_frame_equal(grouped_messages, grouped_messages_after_recompute)

    tabulated_messages_after_recompute_2_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}
        """
    )
    assert_tabulated_messages_are_equal(
        tabulated_messages_df, tabulated_messages_after_recompute_2_df
    )
    # Check that the processed_at is greater than the previous processed_at
    recompute_2_processed_at = tabulated_messages_after_recompute_2_df[
        "phoenix_processed_at"
    ].unique()
    # Make sure that all the processed_at values are the same
    assert recompute_2_processed_at.shape[0] == 1
    # Make sure that the recompute processed_at is greater than the previous recompute processed_at
    assert recompute_2_processed_at[0] > recompute_processed_at[0]
    assert tabulated_messages_after_recompute_2_df["phoenix_job_run_id"].unique() == [11]

    # Testing classified messages

    # Manually create and add some classified_messages
    # Grab rows just to make a dataframe
    classified_messages_df = deduped_messages_df.iloc[:7][["phoenix_platform_message_id"]].copy()
    # Explicitly set the message IDs - this is brittle, but better than doing anything smart.
    classified_messages_df["phoenix_platform_message_id"] = [
        normalisers.anonymize("818337297005563"),  # post with no comments one class
        # post with 4 comments two classes
        normalisers.anonymize("823003113189049"),
        normalisers.anonymize("823003113189049"),
        # comment one class
        normalisers.anonymize("Y29tbWVudDo4MjMwMDMxMTMxODkwNDlfMTM1Njc3Njg4NDk5NzU1Mg=="),
        # comment two classes
        normalisers.anonymize("Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfMTUyMDM5OTc0ODU5MzY2NA=="),
        normalisers.anonymize("Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfMTUyMDM5OTc0ODU5MzY2NA=="),
        normalisers.anonymize("Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfMTUyMDM5OTc0ODU5MzY2NA=="),
    ]
    classified_messages_df["classifier_id"] = 1
    classified_messages_df["classifier_version_id"] = [2, 2, 2, 2, 2, 2, 1]
    # Add an apostrophe to the class_name to test that we don't get sql errors
    classified_messages_df["class_name"] = [
        "d'economy",
        "d'economy",
        "politics",
        "politics",
        "d'economy",
        "politics",
        "old_version_example",
    ]
    classified_messages_df["job_run_id"] = 5
    # Include a duplicated row to test this doesn't affect results
    classified_messages_df = pd.concat([classified_messages_df, classified_messages_df.iloc[0:1]])
    pipeline_jobs_utils.write_data(
        df=classified_messages_df,
        dataset=test_project_namespace,
        table=constants.CLASSIFIED_MESSAGES_TABLE_NAME,
    )

    active_classifiers_versions = [(1, 2)]
    # Re-tabulate, now with the classified messages
    tabulate_flow.tabulate_flow(
        job_run_id=4,
        project_namespace=test_project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )

    tabulated_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}
        """
    )
    # This is a bit complicated, so always best to look at the actual tables in BQ if in any doubt.
    # In classified messages we did the following:
    # - Add a single class to a post which doesn't have any comments -> no change in count
    # - Add two classes to a post, BUT, that post has 4 comments, so it creates 2 * num_comments,
    # i.e. 4 _new_ rows in tabulated_messages table due to cross-product posts x comments.
    # - Add a single class to a comment -> no change in count
    # - Added two classes to a comment -> +1 to the total count
    assert len(tabulated_messages_df) == 20
    assert tabulated_messages_df["post_class"].isna().sum() == 11
    for class_name in ["d'economy", "politics"]:
        assert class_name in tabulated_messages_df["post_class"].unique()
    assert tabulated_messages_df["comment_class"].isna().sum() == 16
    for class_name in ["d'economy", "politics"]:
        assert class_name in tabulated_messages_df["comment_class"].unique()

    # Testing author manual classifications

    # Manually create and add some manually_classified_authors
    manual_post_classifier = {
        "id": 2,
        "project_id": 1,
        "name": "test_manual_authors_classifier",
        "description": "Test manual authors classifier",
        "type": "manual_post_authors",
        "latest_version": {
            "version_id": 1,
            "classifier_id": 1,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "classes": [
                {"name": "news_outlet", "description": "News outlets"},
                {"name": "journalist", "description": "Journalists"},
                {"name": "individual", "description": "Individuals"},
                {"name": "blogger", "description": "Bloggers"},
            ],
            "params": {
                "author_classes": [
                    {
                        "class_name": "news_outlet",
                        "phoenix_platform_message_author_id": normalisers.anonymize(
                            "100064878993116"
                        ),
                    },
                    {
                        "class_name": "news_outlet",
                        "phoenix_platform_message_author_id": normalisers.anonymize(
                            "100064381045972"
                        ),
                    },
                    {
                        "class_name": "journalist",
                        "phoenix_platform_message_author_id": normalisers.anonymize(
                            "100064381045972"
                        ),
                    },
                    {
                        "class_name": "individual",
                        "phoenix_platform_message_author_id": normalisers.anonymize(
                            "100024915288912"
                        ),
                    },
                    {
                        "class_name": "blogger",
                        "phoenix_platform_message_author_id": normalisers.anonymize(
                            "100024915288912"
                        ),
                    },
                ]
            },
        },
    }
    asyncio.run(
        classify_flow.classify_flow(
            classifier_dict=manual_post_classifier,
            project_namespace=test_project_namespace,
            job_run_id=5,
        )
    )
    active_classifiers_versions = [(1, 2), (2, 1)]

    # Re-tabulate, now with the classified authors
    tabulate_flow.tabulate_flow(
        job_run_id=5,
        project_namespace=test_project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )
    tabulated_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}
        """
    )
    assert len(tabulated_messages_df) == 37
    post_author_class_value_counts = tabulated_messages_df["post_author_class"].value_counts()
    assert post_author_class_value_counts["news_outlet"] == 20
    assert post_author_class_value_counts["journalist"] == 16
    comment_author_class_value_counts = tabulated_messages_df[
        "comment_author_class"
    ].value_counts()
    assert comment_author_class_value_counts["individual"] == 2
    assert comment_author_class_value_counts["blogger"] == 2

    # Assert quality checks are working, currently they run with the tabulate flow
    # One orphaned comment is in the test data
    orphaned_comments_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.DATA_QUALITY_ORPHANED_COMMENTS_TABLE_NAME}
        """
    )
    assert len(orphaned_comments_df) == 1

    # Missing authors checks which authors have posts but not in some months
    missing_author_posts_df = pandas_gbq.read_gbq(
        f"""
            SELECT *
            FROM {test_project_namespace}.{constants.DATA_QUALITY_MISSING_AUTHOR_POSTS_TABLE_NAME}
            ORDER BY post_year, post_month
            """
    ).reset_index(drop=True)
    expected_missing_authors = pd.DataFrame(
        {
            "post_author_id": [
                "44f1a515-b823-0a45-cb66-2c6226fef283",
                "44f1a515-b823-0a45-cb66-2c6226fef283",
            ],
            "post_author_name_pi": ["United Nations", "United Nations"],
            "post_author_link_pi": [pd.NA, pd.NA],
            "post_year": [2024, 2024],
            "post_month": [2, 3],
        }
    )
    pd.testing.assert_frame_equal(
        expected_missing_authors, missing_author_posts_df, check_like=True, check_dtype=False
    )

    # Delete just the comments
    gather_id_of_comments = example_gathers.facebook_comments_gather_example().id
    delete_gather_tabulate_flow.delete_gather_tabulate_flow(
        project_id=1,
        job_source_id=gather_id_of_comments,
        job_run_id=6,
        project_namespace=test_project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )

    # Checking that the comments are deleted from the batches
    batches_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GATHER_BATCHES_TABLE_NAME}"
    )
    assert len(batches_df) == 2
    assert gather_id_of_comments not in batches_df["gather_id"].unique()

    # Now the comments should be out of the generalised message table
    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    # There where 25 messages before the comments were deleted
    # So there should be 25 - 9 = 16 messages
    assert len(messages_df) == 16
    assert gather_id_of_comments not in messages_df["gather_id"].unique()

    # and the deduplication should be the same as without the comments, but now with author classes
    deduped_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}
        """
    )
    assert len(deduped_messages_df) == 8
    assert gather_id_of_comments not in deduped_messages_df["gather_id"].unique()

    deduped_authors_after_delete_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_AUTHORS_TABLE_NAME}
        ORDER BY post_count DESC, comment_count DESC
        """
    )
    assert len(deduped_authors_after_delete_df) == 2
    assert deduped_authors_after_delete_df.iloc[0]["post_count"] == 4
    assert deduped_authors_after_delete_df.iloc[0]["comment_count"] == 0

    tabulated_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.TABULATED_MESSAGES_TABLE_NAME}
        """
    )
    assert len(tabulated_messages_df) == 14


def test_danek_facebook_searches_posts(tmp_bq_project):
    """Test pipeline integration with bigquery.

    WARNING: !!!!!!!!!!!!!!
    The patch settings fixture/monkey patching env vars does not work with Prefect flows.

    This test creates a Bigquery dataset with name `test_<random_prefix>`.

    Then runs a gather flow for danek_facebook_searches_posts using sample example data.
    """
    if config.settings.USE_MOCK_BQ:
        raise Exception(
            "This test requires USE_MOCK_BQ to be set to False. "
            "Please change this in python/projects/phiphi/docker_env.dev."
        )

    test_project_namespace = tmp_bq_project

    batch_size = 20
    batch_of_batches_size = 2

    pipeline_result = gather_flow.gather_flow(
        gather_dict=example_gathers.danek_facebook_searches_posts_gather_example().dict(),
        gather_child_type=example_gathers.danek_facebook_searches_posts_gather_example().child_type,
        job_run_id=1,
        project_namespace=test_project_namespace,
        max_mb_batch_size=batch_size,
        batch_of_batches_size=batch_of_batches_size,
    )
    assert pipeline_result is not None
    # Default costs of 1.2 per 1000
    assert pipeline_result.cost == 0.0084
    # There is one error that is skipped in the normalisation
    assert pipeline_result.result_count == 7

    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    assert len(messages_df) == 6


def test_danek_instagram_chained_posts_comments(tmp_bq_project):
    """Test that gather_flow chains a DanekInstagramPosts then DanekInstagramComments gather.

    WARNING: !!!!!!!!!!!!!!
    The patch settings fixture/monkey patching env vars does not work with Prefect flows.

    This test creates a Bigquery dataset with name `test_<random_prefix>`.

    Uses mock danek data (USE_MOCK_DANEK=True). After the posts gather completes,
    selectors.get_post_ids_with_comments queries the real BQ dataset and the returned post IDs
    are used to configure the chained comments gather.
    """
    if config.settings.USE_MOCK_BQ:
        raise Exception(
            "This test requires USE_MOCK_BQ to be set to False. "
            "Please change this in python/projects/phiphi/docker_env.dev."
        )

    test_project_namespace = tmp_bq_project

    batch_size = 20
    batch_of_batches_size = 2

    gather = example_gathers.danek_instagram_posts_with_comments_gather_example()
    pipeline_result = gather_flow.gather_flow(
        gather_dict=gather.dict(),
        gather_child_type=gather.child_type,
        job_run_id=1,
        project_namespace=test_project_namespace,
        max_mb_batch_size=batch_size,
        batch_of_batches_size=batch_of_batches_size,
    )

    assert pipeline_result is not None
    # NOTE: result_count and cost should be verified empirically on first run and updated here.
    # result_count = number of batches written to the write manager (1 post batch + 2 comment
    # batches). cost = (1 + 2) items * 5 / 100_000 = 0.00015
    assert pipeline_result.result_count == 3
    assert pipeline_result.cost == pytest.approx(0.00015)
    assert pipeline_result.is_cost_estimated is False

    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    )
    # 12 = 3 posts (normalised by posts gather) + 3 posts + 6 comments (re-normalised by comments
    # gather, which reuses the same gather_id and picks up all batches for that gather/job_run).
    # The duplicate post normalisation is a known limitation of the chained gather design.
    assert len(messages_df) == 12

    gather_types_in_bq = set(messages_df["gather_type"].unique())
    assert "danek_instagram_posts" in gather_types_in_bq
    assert "danek_instagram_comments" in gather_types_in_bq

    deduped_messages_df = pandas_gbq.read_gbq(
        f"""
        SELECT *
        FROM {test_project_namespace}.{constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}
        """
    )
    # 3 unique posts + 6 unique comments
    assert len(deduped_messages_df) == 9

    post_ids = selectors.get_post_ids_with_comments(
        bigquery_dataset=test_project_namespace,
        gather_id=gather.id,
        gather_type=gather.child_type,
    )
    # Three posts in the mock data, but only two have comments, so should return 2 post IDs
    assert len(post_ids) == 2
    assert all(isinstance(pid, str) for pid in post_ids)
