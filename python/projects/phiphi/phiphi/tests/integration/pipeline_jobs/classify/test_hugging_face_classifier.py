"""Integration tests for the Hugging Face classifier pipeline job."""

import datetime

import pandas as pd
import pandas_gbq
import pytest
from pandas.testing import assert_frame_equal

from phiphi import config
from phiphi.api.projects.classifiers import base_schemas, bucketing_schemas
from phiphi.api.projects.classifiers.hugging_face import schemas
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs import utils as pipeline_utils
from phiphi.pipeline_jobs.classify import hugging_face_classifier


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hf_classifier_integration(tmp_bq_project, monkeypatch):
    """End-to-end integration test for the Hugging Face classifier pipeline job.

    1) Ensure real BigQuery is used.
    2) Use a temporary BigQuery project namespace and overwrite GCS settings via fixtures.
    3) Seed source table with two unclassified messages (m1, m2), one already classified (m_pre).
    4) Seed destination table with:
       a) Two rows for m_pre by this classifier/version (should be skipped).
       b) One row for m2 by a different classifier/version (should NOT be skipped).
    5) Define a dummy HuggingFaceClassifierPipeline with a catch-all bucketing_config.
    6) Patch invoke_hf_flow to write a Parquet of raw scores for m1 and m2 to GCS (4 rows).
    7) Call hugging_face_classifier.classify(...) and capture num_rows_written.
    8) Query classified_messages and compare full contents via assert_frame_equal.
    """
    # 1) Guard against mock BQ
    if config.settings.USE_MOCK_BQ:
        raise Exception("This test requires USE_MOCK_BQ=False; please set in docker_env.dev")

    # 2) Seed source table
    messages = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["m1", "m2", "m_pre"],
            "pi_text": ["foo", "bar", "baz"],
        }
    )
    pipeline_utils.write_data(
        df=messages,
        dataset=tmp_bq_project,
        table=constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME,
    )

    # 3a) Pre-seed classified_messages with some existing data from the classifier
    pre_hf = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["m_pre", "m_pre"],
            "classifier_id": [42, 42],
            "classifier_version_id": [1, 1],
            "class_name": ["low_foo", "high_foo"],
            "class_probability": [0.1, 0.9],
            "job_run_id": [999, 999],
        }
    )
    # 3b) Pre-seed classified_messages with some data from a different classifier
    pre_other = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["m2"],
            "classifier_id": [99],
            "classifier_version_id": [9],
            "class_name": ["old_label"],
            "class_probability": [0.5],
            "job_run_id": [888],
        }
    )
    pipeline_utils.write_data(
        df=pd.concat([pre_hf, pre_other], ignore_index=True),
        dataset=tmp_bq_project,
        table=constants.CLASSIFIED_MESSAGES_TABLE_NAME,
    )

    # 4) Build dummy classifier pipeline object
    version = schemas.HuggingFaceVersionResponse(
        classifier_id=42,
        version_id=1,
        created_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
        updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
        params=schemas.HuggingFaceParams(model_id="dummy-model"),
    )
    classifier = schemas.HuggingFaceClassifierPipeline(
        id=42,
        project_id=1,
        name="test-hf",
        description="Test HF",
        type=base_schemas.ClassifierType.hugging_face,
        latest_version=version,
    )

    # 5) Write a stray parquet for a different run_id—should be ignored
    junk_path = constants.HF_RESULTS_URI_TEMPLATE.format(
        bucket=config.settings.HF_GCS_BUCKET_NAME,
        prefix=tmp_bq_project,
        job_run_id=9999,
    )
    pd.DataFrame([{"id": "x", "label": "junk", "score": 1.0}]).to_parquet(junk_path, index=False)

    # 6) Patch invoke_hf_flow to write only our run's parquet
    async def fake_invoke(
        input_uri: str, output_uri: str, failed_uri: str, model_id: str, logger
    ) -> bool:
        # Create a DataFrame with raw scores for both labels for both messages
        df_out = pd.DataFrame(
            {
                "id": ["m1", "m1", "m2", "m2"],
                "label": ["foo_label", "bar_label", "foo_label", "bar_label"],
                "score": [0.1, 0.3, 0.6, 0.8],
            }
        )
        # write directly to the exact path
        df_out.to_parquet(output_uri, index=False)
        return True

    monkeypatch.setattr(hugging_face_classifier, "invoke_hf_flow", fake_invoke)

    # 7) Run classification
    result = await hugging_face_classifier.classify(
        classifier=classifier,
        bigquery_dataset=tmp_bq_project,
        job_run_id=1234,
    )
    assert result["num_rows_written"] == 4

    # 8) Verify final classified_messages contents
    final_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_bq_project}.{constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )
    assert len(final_df) == 7  # 2 pre_hf + 1 pre_other + 4 new

    # Build expected DataFrame
    expected = pd.DataFrame(
        [
            # pre_hf rows
            {
                "phoenix_platform_message_id": "m_pre",
                "classifier_id": 42,
                "classifier_version_id": 1,
                "class_name": "low_foo",
                "class_probability": 0.1,
                "job_run_id": 999,
            },
            {
                "phoenix_platform_message_id": "m_pre",
                "classifier_id": 42,
                "classifier_version_id": 1,
                "class_name": "high_foo",
                "class_probability": 0.9,
                "job_run_id": 999,
            },
            # pre_other row
            {
                "phoenix_platform_message_id": "m2",
                "classifier_id": 99,
                "classifier_version_id": 9,
                "class_name": "old_label",
                "class_probability": 0.5,
                "job_run_id": 888,
            },
            # new for m1
            {
                "phoenix_platform_message_id": "m1",
                "classifier_id": 42,
                "classifier_version_id": 1,
                "class_name": "low_prob_foo_label",
                "class_probability": 0.1,
                "job_run_id": 1234,
            },
            {
                "phoenix_platform_message_id": "m1",
                "classifier_id": 42,
                "classifier_version_id": 1,
                "class_name": "medium_prob_bar_label",
                "class_probability": 0.3,
                "job_run_id": 1234,
            },
            # new for m2
            {
                "phoenix_platform_message_id": "m2",
                "classifier_id": 42,
                "classifier_version_id": 1,
                "class_name": "high_prob_foo_label",
                "class_probability": 0.6,
                "job_run_id": 1234,
            },
            {
                "phoenix_platform_message_id": "m2",
                "classifier_id": 42,
                "classifier_version_id": 1,
                "class_name": "very_high_prob_bar_label",
                "class_probability": 0.8,
                "job_run_id": 1234,
            },
        ]
    )

    # Sort & compare
    cols = [
        "phoenix_platform_message_id",
        "classifier_id",
        "classifier_version_id",
        "class_name",
        "class_probability",
        "job_run_id",
    ]
    actual_sorted = final_df[cols].sort_values(cols).reset_index(drop=True)
    expected_sorted = expected[cols].sort_values(cols).reset_index(drop=True)
    assert_frame_equal(actual_sorted, expected_sorted, check_dtype=False)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_no_unclassified_rows(tmp_bq_project, monkeypatch):
    """Test that classify returns early with 0 rows when all messages are already classified.

    - Seed source table with one message m1.
    - Pre-seed classified_messages with a row for m1 by this classifier/version.
    - Run classify() and verify:
      1. It returns num_rows_written=0
      2. invoke_hf_flow is never called (monkeypatch to fail if called)
      3. No new rows are written to classified_messages
    """
    # require real BQ
    if config.settings.USE_MOCK_BQ:
        pytest.skip("Requires real BigQuery")

    # 1) Seed source table with one message
    messages = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["m1"],
            "pi_text": ["foo"],
        }
    )
    pipeline_utils.write_data(
        df=messages,
        dataset=tmp_bq_project,
        table=constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME,
    )

    # 2) Pre-seed classified_messages with a row for m1
    pre_classified = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["m1"],
            "classifier_id": [42],
            "classifier_version_id": [1],
            "class_name": ["existing_class"],
            "class_probability": [0.9],
            "job_run_id": [999],
        }
    )
    pipeline_utils.write_data(
        df=pre_classified,
        dataset=tmp_bq_project,
        table=constants.CLASSIFIED_MESSAGES_TABLE_NAME,
    )

    # 3) Build classifier object
    version = schemas.HuggingFaceVersionResponse(
        classifier_id=42,
        version_id=1,
        created_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
        updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
        params=schemas.HuggingFaceParams(model_id="dummy-model"),
    )
    classifier = schemas.HuggingFaceClassifierPipeline(
        id=42,
        project_id=1,
        name="test-hf",
        description="Test HF",
        type=base_schemas.ClassifierType.hugging_face,
        latest_version=version,
    )

    # 4) Patch invoke_hf_flow to fail if called (it shouldn't be)
    async def should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "invoke_hf_flow should not be called when there are no unclassified rows"
        )

    monkeypatch.setattr(hugging_face_classifier, "invoke_hf_flow", should_not_be_called)

    # 5) Run classification
    result = await hugging_face_classifier.classify(
        classifier=classifier,
        bigquery_dataset=tmp_bq_project,
        job_run_id=1234,
    )

    # 6) Verify early return with 0 rows
    assert result["num_rows_written"] == 0

    # 7) Verify no new rows were written
    final_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_bq_project}.{constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )
    assert len(final_df) == 1  # Only the pre-seeded row
    assert final_df.iloc[0]["phoenix_platform_message_id"] == "m1"
    assert final_df.iloc[0]["classifier_id"] == 42
    assert final_df.iloc[0]["classifier_version_id"] == 1
    assert final_df.iloc[0]["class_name"] == "existing_class"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_custom_bucketing(tmp_bq_project, monkeypatch):
    """Tests that a custom bucketing config produces the correct buckets in BigQuery.

    - Seed two messages m1, m2.
    - Define two BucketingConfig: one for foo_label, one for bar_label.
    - Fake the HF flow to output one score per message per label.
    - Run classify() and assert exactly 4 bucketed rows with correct thresholds.
    """
    # require real BQ
    if config.settings.USE_MOCK_BQ:
        pytest.skip("Requires real BigQuery")

    # 1) Seed source table with two messages
    df_src = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["m1", "m2"],
            "pi_text": ["alpha", "beta"],
        }
    )
    pipeline_utils.write_data(
        df=df_src,
        dataset=tmp_bq_project,
        table=constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME,
    )

    # 2) No pre-seeded classified rows

    # 3) Build classifier with custom bucketing configs
    params = schemas.HuggingFaceParams(
        model_id="dummy",
        bucketing_configs=[
            bucketing_schemas.BucketingConfig(
                class_name="foo_label",
                buckets=[
                    bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                    bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                ],
            ),
            bucketing_schemas.BucketingConfig(
                class_name="bar_label",
                buckets=[
                    bucketing_schemas.BucketThreshold(name="medium", upper_threshold=0.7),
                    bucketing_schemas.BucketThreshold(name="very_high", upper_threshold=1.0),
                ],
            ),
        ],
    )
    version = schemas.HuggingFaceVersionResponse(
        classifier_id=123,
        version_id=1,
        created_at=datetime.datetime(2021, 1, 1),
        updated_at=datetime.datetime(2021, 1, 1),
        params=params,
    )
    classifier = schemas.HuggingFaceClassifierPipeline(
        id=123,
        project_id=1,
        name="custom-bucket-test",
        description="Test custom bucketing",
        type=base_schemas.ClassifierType.hugging_face,
        latest_version=version,
    )

    # 4) Patch invoke_hf_flow to emit one score per message per label
    async def fake_invoke(_input, output_uri, failed_uri, _model, logger):
        # write Parquet with four rows: (m1,foo,0.4),(m1,bar,0.8),(m2,foo,0.6),(m2,bar,0.5)
        df_out = pd.DataFrame(
            [
                {"id": "m1", "label": "foo_label", "score": 0.4},
                {"id": "m1", "label": "bar_label", "score": 0.8},
                {"id": "m2", "label": "foo_label", "score": 0.6},
                {"id": "m2", "label": "bar_label", "score": 0.5},
            ]
        )
        df_out.to_parquet(output_uri, index=False)

    monkeypatch.setattr(hugging_face_classifier, "invoke_hf_flow", fake_invoke)

    # 5) Run classification
    result = await hugging_face_classifier.classify(
        classifier=classifier,
        bigquery_dataset=tmp_bq_project,
        job_run_id=555,
    )
    written = result["num_rows_written"]
    assert written == 4

    # 6) Read back and verify buckets:
    final = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_bq_project}.{constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )
    # Expect rows:
    expected = pd.DataFrame(
        [
            # m1 → score=0.4 → low_foo_label
            {
                "phoenix_platform_message_id": "m1",
                "class_name": "low_foo_label",
                "class_probability": 0.4,
            },
            # m1 → score=0.8 → very_high_bar_label
            {
                "phoenix_platform_message_id": "m1",
                "class_name": "very_high_bar_label",
                "class_probability": 0.8,
            },
            # m2 → score=0.6 → high_foo_label
            {
                "phoenix_platform_message_id": "m2",
                "class_name": "high_foo_label",
                "class_probability": 0.6,
            },
            # m2 → score=0.5 → medium_bar_label
            {
                "phoenix_platform_message_id": "m2",
                "class_name": "medium_bar_label",
                "class_probability": 0.5,
            },
        ]
    )
    # Filter final for only new classifier rows
    new = final.query("classifier_id==123 and classifier_version_id==1")
    cols = ["phoenix_platform_message_id", "class_name", "class_probability"]
    actual_sorted = new[cols].sort_values(cols).reset_index(drop=True)
    expected_sorted = expected[cols].sort_values(cols).reset_index(drop=True)
    assert_frame_equal(actual_sorted, expected_sorted, check_dtype=False)
