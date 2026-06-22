"""Inference flows for Hugging Face classifier."""

from typing import Literal

import prefect

from hugging_face_classifier import inference


@prefect.flow(name="inference_classify_flow", result_serializer="json")
def inference_classify_flow(
    input_file_path: str,
    output_file_path: str,
    failed_records_file_path: str,
    model_name: str,
    batch_size: int = 500,
    text_column: str = "text",
    id_column: str = "id",
    compression: Literal["gzip", "bz2", "brotli", "lz4", "zstd", "snappy", "none"] = "snappy",
) -> inference.HFClassificationResult:
    """Flow to run inference on a dataset using a Hugging Face classifier.

    Args:
        input_file_path (str): Path to the input Parquet file.
        output_file_path (str): Path to save the classification results.
        failed_records_file_path (str): Path to save records that failed classification.
        model_name (str): Name of the Hugging Face model to use for classification.
        batch_size (int, optional): Batch size for processing. Defaults to 32.
        text_column (str, optional): Column name containing text data. Defaults to "text".
        id_column (str, optional): Column name containing IDs. Defaults to "id".
        compression (Literal, optional): Compression type for output file. Defaults to "snappy".

    Returns:
        infer.HFClassificationResult: Result object containing classification statistics.
    """
    logger = prefect.get_run_logger()
    logger.info("Starting inference flow.")

    # Run the classification
    result = inference.classify_text_streaming(
        input_file_path=input_file_path,
        output_file_path=output_file_path,
        failed_records_file_path=failed_records_file_path,
        model_name=model_name,
        batch_size=batch_size,
        text_column=text_column,
        id_column=id_column,
        compression=compression,
        logger=logger,
    )

    logger.info(
        f"Inference completed with {result.total_successfully_processed} successful "
        f"and {result.total_failed_to_process} failed classifications in "
        f"{result.duration_seconds:.2f} seconds."
    )
    return result
