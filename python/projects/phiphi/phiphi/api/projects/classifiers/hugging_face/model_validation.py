"""Hugging Face Model Validation Module.

This module provides functionality to validate Hugging Face models based on specific criteria.
"""

import fastapi
import huggingface_hub

from phiphi import config


class InvalidModelError(fastapi.HTTPException):
    """Custom exception for invalid Hugging Face models."""

    def __init__(self, error_key: str, message: str) -> None:
        """Constructor for custom exception."""
        super().__init__(
            status_code=400,
            detail={"error_key": error_key, "message": message},
            headers={"error_key": error_key},
        )


def is_valid_model(model_id: str) -> bool:
    """Validate a Hugging Face model against several criteria.

    This function checks the following conditions:
    1. The model exists on the Hugging Face Hub.
    2. The model architecture includes any <X>ForSequenceClassification class.
    3. The model repository contains at least one top-level .safetensors file,
       or, if none, at least one top-level .bin file (PyTorch weights).

    There are (undocumented) limits to the usage of hugging face hug when not authenticated. Use
    HF_TOKEN environment variable to authenticate if necessary.

    Args:
        model_id: The identifier of the model on the Hugging Face Hub.

    Returns:
        True if all checks pass; otherwise raises InvalidModelError with error details.
    """
    if model_id in config.settings.HUGGING_FACE_MODELS_WHITELIST:
        return True

    api = huggingface_hub.HfApi()

    # 1. Check existence on Hugging Face Hub
    try:
        model_info = api.model_info(model_id, expand=["config"])
    except huggingface_hub.errors.RepositoryNotFoundError:
        raise InvalidModelError(
            error_key="model_not_found",
            message=f"Model '{model_id}' not found on the Hugging Face Hub.",
        )
    except huggingface_hub.errors.HFValidationError:
        raise InvalidModelError(
            error_key="invalid_model_id",
            message=f"Invalid model ID '{model_id}'.",
        )

    # 2. Check architecture for SequenceClassification
    model_config = model_info.config or {}
    architectures = model_config.get("architectures", [])
    if not any(arch.endswith("ForSequenceClassification") for arch in architectures):
        raise InvalidModelError(
            error_key="invalid_architecture",
            message=f"Model '{model_id}' does not have a SequenceClassification architecture.",
        )

    # 3. Check there are files in the repository
    try:
        _ = api.list_repo_files(model_id)
    except Exception as exc:
        raise InvalidModelError(
            error_key="list_repo_files_failed",
            message=str(exc),
        )

    # 3a. Check safetensors
    try:
        api.get_safetensors_metadata(model_id)
    except huggingface_hub.errors.NotASafetensorsRepoError:
        raise InvalidModelError(
            error_key="no_safetensors",
            message=(
                f"Model '{model_id}' does not have any '.safetensors' weight files "
                "at the top level of the repository."
            ),
        )

    return True
