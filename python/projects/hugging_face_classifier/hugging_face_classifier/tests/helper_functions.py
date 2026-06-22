"""Helper functions for tests."""

import os
import typing

import datasets
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import hugging_face_classifier.inference as inference


def assert_streaming_results(  # type: ignore[no-any-unimported]
    results_df: pd.DataFrame,
    sample_dataset: datasets.Dataset,
    model_name: str,
    data_source: str,
    failed_df: typing.Optional[pd.DataFrame] = None,
):
    """Helper function to assert on the classification results from a DataFrame.

    Args:
        results_df: DataFrame containing successful classification results
        sample_dataset: Original sample dataset
        model_name: Name of the model used for classification
        data_source: Name of the data source
        failed_df: Optional DataFrame containing failed records
    """
    assert isinstance(results_df, pd.DataFrame)

    # Get the total number of expected records
    total_expected = len(sample_dataset)
    total_results = len(results_df)
    total_failed = len(failed_df) if failed_df is not None else 0

    # Check that all records are accounted for (either successful or failed)
    assert total_results + total_failed == total_expected, (
        f"Total processed records ({total_results + total_failed}) should match "
        f"sample_dataset size ({total_expected}) "
        f"for {model_name} with {data_source} data."
    )

    # Check result dataframe structure
    assert "id" in results_df.columns, "Results missing 'id' column"
    assert "score" in results_df.columns, "Results missing 'score' column"
    assert "label" in results_df.columns, "Results missing 'label' column"


def run_classification_test(  # type: ignore[no-any-unimported]
    input_file_path: str,
    output_dir: str,
    model_name: str,
    sample_dataset: datasets.Dataset,
    batch_size: int = 2,
    data_source_name: str = "test_data",
):
    """Run classification test and assert results.

    Args:
        input_file_path: Path to input file (local or GCS)
        output_dir: Directory to store output
        model_name: Name of the model to test
        sample_dataset: Sample dataset to compare results with
        batch_size: Batch size for processing
        data_source_name: Name identifier for the data source for logging

    Returns:
        Path to the output file
    """
    output_file_path = os.path.join(output_dir, f"output_{data_source_name}.parquet")
    failed_records_path = os.path.join(output_dir, f"failed_{data_source_name}.parquet")

    # Run the classification
    result = inference.classify_text_streaming(
        input_file_path=input_file_path,
        output_file_path=output_file_path,
        model_name=model_name,
        batch_size=batch_size,
        text_column="text",
        id_column="id",
        failed_records_file_path=failed_records_path,
    )

    # Check that all records were processed (either successfully or as failures)
    assert result.total_successfully_processed + result.total_failed_to_process == len(
        sample_dataset
    ), (
        f"Total processed records ("
        f"{result.total_successfully_processed + result.total_failed_to_process}) "
        f"should match sample_dataset size ({len(sample_dataset)})"
    )

    # Read the results
    results_df = pq.read_table(output_file_path).to_pandas()

    # Read failed records if they exist
    failed_df = None
    if os.path.exists(failed_records_path) and os.path.getsize(failed_records_path) > 0:
        failed_df = pq.read_table(failed_records_path).to_pandas()

    # Assert on the results
    assert_streaming_results(results_df, sample_dataset, model_name, data_source_name, failed_df)

    return output_file_path


def create_local_test_file(sample_dataset: datasets.Dataset, temp_dir: str):  # type: ignore[no-any-unimported]
    """Create a local Parquet test file from sample data.

    Args:
        sample_dataset: Sample dataset to write to file
        temp_dir: Directory to store the file

    Returns:
        Path to the created file
    """
    input_file_path = os.path.join(temp_dir, "input.parquet")

    # Ensure all records have the required columns
    for record in sample_dataset:
        if "id" not in record:
            raise ValueError("Sample dataset is missing 'id' column")
        if "text" not in record:
            raise ValueError("Sample dataset is missing 'text' column")

    # Create the table and write to Parquet
    table = pa.Table.from_pylist(sample_dataset)
    pq.write_table(table, input_file_path)

    return input_file_path
