"""Unit tests for the Hugging Face Classifier module."""

import unittest.mock

import pandas as pd
import pytest

import hugging_face_classifier.inference as inference
import hugging_face_classifier.tests.conftest as hf_conftest
import hugging_face_classifier.tests.helper_functions as hf_test_helpers


@pytest.mark.parametrize("model_name", hf_conftest.MODEL_NAMES)
def test_create_classifier_pipeline_unit(model_name):
    """Tests successful creation of the classifier pipeline."""
    try:
        classifier = inference.create_classifier_pipeline(model_name)
        assert callable(classifier), "Pipeline should be callable"
    except Exception as e:
        pytest.fail(f"Pipeline creation failed for '{model_name}': {e}")


def test_create_classifier_pipeline_invalid_model_unit():
    """Tests pipeline creation failure with an invalid model name."""
    model_name = "this_model_does_not_exist"
    with pytest.raises(RuntimeError, match="Failed to load model or tokenizer"):
        inference.create_classifier_pipeline(model_name)


@pytest.mark.parametrize("model_name", hf_conftest.MODEL_NAMES)
def test_classify_text_local(model_name, sample_dataset, tmpdir):
    """Tests text classification with a streaming dataset from a local file."""
    input_file_path = hf_test_helpers.create_local_test_file(sample_dataset, tmpdir)

    hf_test_helpers.run_classification_test(
        input_file_path=input_file_path,
        output_dir=tmpdir,
        model_name=model_name,
        sample_dataset=sample_dataset,
        batch_size=2,
        data_source_name="local_file",
    )


def test_classification_result_dataclass():
    """Test HFClassificationResult dataclass initialization and attributes."""
    result = inference.HFClassificationResult()
    assert result.total_successfully_processed == 0
    assert result.total_failed_to_process == 0
    assert result.duration_seconds == 0

    result = inference.HFClassificationResult(
        total_successfully_processed=10, total_failed_to_process=5, duration_seconds=15.5
    )
    assert result.total_successfully_processed == 10
    assert result.total_failed_to_process == 5
    assert result.duration_seconds == 15.5


def test_missing_text_column(tmp_path):
    """Test that missing text column raises an appropriate error."""
    output_path = str(tmp_path / "output.parquet")
    failed_records_path = str(tmp_path / "failed.parquet")
    missing_columns_df = pd.DataFrame(
        {
            "other_id": ["1", "2", "3"],
            "other_text": ["Sample text 1", "Sample text 2", "Sample text 3"],
        }
    )
    missing_columns_file_path = str(tmp_path / "missing_columns.parquet")
    missing_columns_df.to_parquet(missing_columns_file_path)

    with pytest.raises(ValueError, match="Column 'text' missing in the Parquet file"):
        inference.classify_text_streaming(
            input_file_path=missing_columns_file_path,
            output_file_path=output_path,
            failed_records_file_path=failed_records_path,
            model_name="bert-base-uncased",
            text_column="text",
            id_column="other_id",
        )


def test_missing_id_column(tmp_path):
    """Test that missing id column raises an appropriate error."""
    output_path = str(tmp_path / "output.parquet")
    failed_records_path = str(tmp_path / "failed.parquet")
    missing_columns_df = pd.DataFrame(
        {
            "other_id": ["1", "2", "3"],
            "text": ["Sample text 1", "Sample text 2", "Sample text 3"],
        }
    )
    missing_columns_file_path = str(tmp_path / "missing_columns.parquet")
    missing_columns_df.to_parquet(missing_columns_file_path)

    with pytest.raises(ValueError, match="Column 'id' missing in the Parquet file"):
        inference.classify_text_streaming(
            input_file_path=missing_columns_file_path,
            output_file_path=output_path,
            failed_records_file_path=failed_records_path,
            model_name="bert-base-uncased",
            text_column="text",
            id_column="id",
        )


def test_process_all_batches_basic():
    """Test process_all_batches returns correct format and processes records."""
    dataset = [
        {"id": "1", "text": "Valid text one"},
        {"id": "2", "text": "Valid text two"},
        {"id": "3", "text": "Valid text three"},
        {"id": "4", "text": ""},  # This should fail
    ]

    # Mock classifier
    mock_classifier = unittest.mock.MagicMock()
    mock_classifier.return_value = [{"score": 0.85, "label": "positive"}]

    # Mock writers
    mock_output_writer = unittest.mock.MagicMock()
    mock_failed_writer = unittest.mock.MagicMock()

    # Test with batch size of 2 to ensure multiple batches are processed
    success_count, failed_count = inference.process_all_batches(
        dataset=dataset,
        batch_size=2,
        classifier=mock_classifier,
        output_writer=mock_output_writer,
        failed_records_writer=mock_failed_writer,
        text_column="text",
        id_column="id",
    )

    # Check return format is tuple of two integers
    assert isinstance(success_count, int), "Success count should be an integer"
    assert isinstance(failed_count, int), "Failed count should be an integer"
    assert success_count == 3, f"Expected 3 successful records, got {success_count}"
    assert failed_count == 1, f"Expected 1 failed record, got {failed_count}"
    assert success_count + failed_count == 4, "Total processed should equal dataset size"

    # Verify output writer was called
    assert mock_output_writer.write_table.call_count == 2, "Output writer should be called"

    # Verify failed writer was called for failed records
    assert mock_failed_writer.write_table.call_count == 1, "Failed writer should be called"


def test_process_all_batches_empty_dataset():
    """Test process_all_batches with empty dataset."""
    dataset = []
    mock_classifier = unittest.mock.MagicMock()
    mock_output_writer = unittest.mock.MagicMock()
    mock_failed_writer = unittest.mock.MagicMock()

    success_count, failed_count = inference.process_all_batches(
        dataset=dataset,
        batch_size=2,
        classifier=mock_classifier,
        output_writer=mock_output_writer,
        failed_records_writer=mock_failed_writer,
        text_column="text",
        id_column="id",
    )

    assert success_count == 0, "Empty dataset should have 0 successful records"
    assert failed_count == 0, "Empty dataset should have 0 failed records"
    mock_output_writer.write_table.assert_not_called()
    mock_failed_writer.write_table.assert_not_called()


def test_process_all_batches_with_none_failed_writer():
    """Test process_all_batches with None failed_records_writer when no failures occur."""
    dataset = [
        {"id": "1", "text": "Valid text one"},
        {"id": "2", "text": "Valid text two"},
    ]

    # Mock classifier
    mock_classifier = unittest.mock.MagicMock()
    mock_classifier.return_value = [{"score": 0.85, "label": "positive"}]

    # Mock output writer
    mock_output_writer = unittest.mock.MagicMock()

    # Test with None failed writer - should work fine when no failures occur
    success_count, failed_count = inference.process_all_batches(
        dataset=dataset,
        batch_size=2,
        classifier=mock_classifier,
        output_writer=mock_output_writer,
        failed_records_writer=None,
        text_column="text",
        id_column="id",
    )

    # Check return format and counts
    assert isinstance(success_count, int), "Success count should be an integer"
    assert isinstance(failed_count, int), "Failed count should be an integer"
    assert success_count == 2, f"Expected 2 successful records, got {success_count}"
    assert failed_count == 0, f"Expected 0 failed records, got {failed_count}"

    # Verify output writer was called for successful records
    assert mock_output_writer.write_table.call_count == 1, "Output writer should be called once"
