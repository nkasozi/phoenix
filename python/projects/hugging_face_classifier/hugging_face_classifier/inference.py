"""Infer classification using hugging face classifier with streaming for large datasets."""

import dataclasses
import itertools
import logging
import time
import typing
from typing import Dict, List, Literal, Optional, Tuple

import datasets
import pyarrow as pa
import pyarrow.parquet as pq
import transformers

from hugging_face_classifier import logging_utils

default_logger = logging_utils.get_module_logger(__name__)


@dataclasses.dataclass
class HFClassificationResult:
    """Result of a classification run with success and failure information."""

    total_successfully_processed: int = 0
    total_failed_to_process: int = 0
    duration_seconds: float = 0


def create_classifier_pipeline(model_name):
    """Creates a text classification pipeline.

    Args:
        model_name (str): Name of the Hugging Face pre-trained model.

    Returns:
        transformers.Pipeline: A Hugging Face text classification pipeline.
    """
    try:
        try:
            tokenizer = transformers.AutoTokenizer.from_pretrained(model_name, use_fast=True)
        except Exception as e:
            logging.warning(f"Fast tokenizer failed ({e}), falling back to slow tokenizer.")
            tokenizer = transformers.AutoTokenizer.from_pretrained(model_name, use_fast=False)
        model = transformers.AutoModelForSequenceClassification.from_pretrained(model_name)
        classifier = transformers.pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            padding=True,
            truncation=True,
            max_length=512,
        )
        return classifier
    except Exception as e:
        raise RuntimeError(f"Failed to load model or tokenizer '{model_name}': {e}")


def process_single_record(
    record: Dict[str, typing.Any], classifier, id_column: str, text_column: str
) -> Tuple[str, float, str]:
    """Process a single record for classification.

    Args:
        record: complete record containing text to classify
        classifier: HuggingFace pipeline classifier
        id_column: Name of ID column
        text_column: Name of text column

    Returns:
        tuple: (record_id, score, label) - The processed results ready for output

    Raises:
        ValueError: If text is invalid or prediction format is incorrect
        RuntimeError: For classifier execution errors
    """
    # Extract record ID and text (assuming columns exist, validated at dataset level)
    record_id = str(record[id_column])
    text = record[text_column]

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Record {record_id}: Empty or non-string text content")

    try:
        prediction = classifier(text)[0]  # Get first prediction
    except Exception as e:
        raise RuntimeError(f"Classifier execution failed for record {record_id}: {str(e)}")

    if not isinstance(prediction, dict) or "score" not in prediction or "label" not in prediction:
        raise ValueError(f"Record {record_id}: Invalid prediction format returned by classifier")

    return record_id, prediction["score"], prediction["label"]


def create_valid_input_dataset(input_file_path: str, text_column: str, id_column: str):
    """Validates that the required columns exist in the input Parquet file.

    Args:
        input_file_path: Path to the input Parquet file. Note, this will work for URI paths that
        contain a * wildcard - it will pick up all files that match the pattern.
        text_column: Name of the column containing text to classify
        id_column: Name of the column containing record IDs

    Returns:
        The prepared dataset ready for streaming

    Raises:
        ValueError: If the input file is empty or missing required columns
    """
    # Stream the dataset rather than loading it all into memory
    dataset = datasets.load_dataset(
        "parquet", data_files=input_file_path, split="train", streaming=True
    )

    # Verify required columns exist by checking the first item
    try:
        first_record_iterator = iter(dataset)
        first_record = next(first_record_iterator)
        for col in (text_column, id_column):
            if col not in first_record:
                raise ValueError(f"Column '{col}' missing in the Parquet file.")
        return dataset
    except StopIteration:
        raise ValueError("Input Parquet file is empty.")


def write_failed_records_batch(
    writer: Optional[pq.ParquetWriter], failed_records: List[Dict[str, typing.Any]]
):
    """Writes a batch of failed records to the Parquet file."""
    if failed_records and writer:  # Check both conditions
        failed_data = {
            "id": [item["id"] for item in failed_records],
            "original_record": [str(item["original_record"]) for item in failed_records],
            "error": [item["error"] for item in failed_records],
        }
        table = pa.Table.from_pydict(failed_data)
        writer.write_table(table)


def process_single_batch(
    batch: List[Dict[str, typing.Any]],
    classifier,
    output_writer: pq.ParquetWriter,
    failed_records_writer: Optional[pq.ParquetWriter],
    text_column: str,
    id_column: str,
) -> Tuple[int, int]:
    """Process a single batch of records for classification."""
    successfully_processed_count = 0
    failed_processed_count = 0
    failed_records: List[Dict[str, typing.Any]] = []
    output_records: Dict[str, List[typing.Any]] = {id_column: [], "score": [], "label": []}

    for record in batch:
        try:
            record_id, score, label = process_single_record(
                record, classifier, id_column, text_column
            )
            output_records[id_column].append(record_id)
            output_records["score"].append(score)
            output_records["label"].append(label)
            successfully_processed_count += 1
        except (ValueError, RuntimeError) as e:
            record_id = str(record.get(id_column, "unknown_id"))
            failed_record_info = {
                "id": record_id,
                "original_record": record,
                "error": str(e),
            }
            failed_records.append(failed_record_info)
            failed_processed_count += 1

    # Write successful records if any
    if output_records[id_column]:
        table = pa.Table.from_pydict(output_records)
        output_writer.write_table(table)

    # Write failed records if any
    if failed_records:
        write_failed_records_batch(failed_records_writer, failed_records)

    return successfully_processed_count, failed_processed_count


def process_all_batches(
    dataset,
    batch_size: int,
    classifier,
    output_writer: pq.ParquetWriter,
    failed_records_writer: Optional[pq.ParquetWriter],
    text_column: str,
    id_column: str,
) -> Tuple[int, int]:
    """Process all batches of records from the dataset, both successful and failed.

    Args:
        dataset: Dataset to process
        batch_size: Size of batches to process
        classifier: HuggingFace classifier pipeline
        output_writer: ParquetWriter for successful outputs
        failed_records_writer: ParquetWriter for failed records
        text_column: Name of the column containing text
        id_column: Name of the column containing record IDs

    Returns:
        tuple: (
            total_successfully_processed: Number of successfully processed records,
            total_failed_to_process: Number of failed records,
        )
    """
    total_successfully_processed = 0
    total_failed_to_process = 0

    dataset_iter = iter(dataset)

    # Calls the function repeatedly until it returns an empty list
    for batch in iter(lambda: list(itertools.islice(dataset_iter, batch_size)), []):
        success_count, fail_count = process_single_batch(
            batch, classifier, output_writer, failed_records_writer, text_column, id_column
        )

        total_successfully_processed += success_count
        total_failed_to_process += fail_count

    return total_successfully_processed, total_failed_to_process


def classify_text_streaming(
    input_file_path: str,
    output_file_path: str,
    failed_records_file_path: str,
    model_name: str,
    batch_size: int = 500,
    text_column: str = "text",
    id_column: str = "id",
    compression: Literal["gzip", "bz2", "brotli", "lz4", "zstd", "snappy", "none"] = "snappy",
    logger: None | logging.Logger | logging.LoggerAdapter = None,
) -> HFClassificationResult:
    """Processes a large dataset by streaming, classifying in batches, and writing incrementally.

    Args:
        input_file_path: Path to the input Parquet file.
        output_file_path: Path to save the output Parquet file.
        failed_records_file_path: Path to save records that failed classification.
        model_name: Name of the Hugging Face model.
        batch_size: Batch size for inference.
        text_column: Name of the column containing text to classify.
        id_column: Name of the column containing record IDs.
        compression: Compression algorithm to use for the output Parquet file.
        logger: Optional logger for logging messages. See `logging_utils` for default
            configuration.

    Returns:
        HFClassificationResult object with statistics about processing.

    Raises:
        RuntimeError: If the classification process fails completely
        ValueError: If the input file is empty or missing required columns
    """
    if logger is None:
        logger = default_logger
    start_time = time.time()
    logger.info("Starting classification process...")
    logger.info(f"Start time: {start_time}")
    result = HFClassificationResult()

    # Load classifier and validate dataset
    logger.info(f"Creating classifier using model: {model_name}")
    classifier = create_classifier_pipeline(model_name)
    logger.info("Classifier pipeline created successfully.")
    logger.info("Creating and validating input dataset...")
    dataset = create_valid_input_dataset(input_file_path, text_column, id_column)
    logger.info("Input dataset created successfully.")

    # Set up schema for output file
    output_schema = pa.schema(
        [
            pa.field(id_column, pa.string()),
            pa.field("score", pa.float64()),
            pa.field("label", pa.string()),  # type: ignore[arg-type]
        ]
    )

    with pq.ParquetWriter(output_file_path, output_schema, compression=compression) as writer:
        # Set up failed records writer if needed
        failed_records_writer = None
        if failed_records_file_path:
            failed_schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("original_record", pa.string()),
                    pa.field("error", pa.string()),
                ]
            )
            failed_records_writer = pq.ParquetWriter(
                failed_records_file_path, failed_schema, compression=compression
            )

        logger.info("Starting to classsify...")
        # Process all records
        result.total_successfully_processed, result.total_failed_to_process = process_all_batches(
            dataset,
            batch_size,
            classifier,
            writer,
            failed_records_writer,
            text_column,
            id_column,
        )

        if failed_records_writer:
            failed_records_writer.close()

    result.duration_seconds = time.time() - start_time
    logger.info(
        f"Classification completed in {result.duration_seconds:.2f} seconds. "
        f"Successfully processed: {result.total_successfully_processed}, "
        f"Failed to process: {result.total_failed_to_process}"
    )
    return result
