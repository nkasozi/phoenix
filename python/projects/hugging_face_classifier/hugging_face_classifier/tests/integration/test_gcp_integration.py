"""Integration tests for the Hugging Face Classifier module."""

import pytest

import hugging_face_classifier.tests.conftest as hf_conftest
import hugging_face_classifier.tests.helper_functions as hf_test_helpers

GCP_BUCKET_NAME_INTEGRATION = "hugging_face_classifier_test_data"
TEST_DATA_GCP_PATH_INTEGRATION = "test_input_data.parquet"


@pytest.mark.parametrize("model_name", hf_conftest.MODEL_NAMES)
def test_classify_text_integration(model_name, sample_dataset, tmpdir):
    """Tests text classification with a file from GCP using streaming."""
    gcs_url = f"gs://{GCP_BUCKET_NAME_INTEGRATION}/{TEST_DATA_GCP_PATH_INTEGRATION}"
    print(f"Attempting to run integration test with GCP data from: {gcs_url} using streaming")

    hf_test_helpers.run_classification_test(
        input_file_path=gcs_url,
        output_dir=tmpdir,
        model_name=model_name,
        sample_dataset=sample_dataset,
        batch_size=4,
        data_source_name="GCP_streaming",
    )
