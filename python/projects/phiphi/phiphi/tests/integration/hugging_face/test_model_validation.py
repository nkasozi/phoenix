"""Test hugging face model validation."""

import os

import pytest

from phiphi.api.projects.classifiers.hugging_face import model_validation

oauth_token = os.getenv("HF_TOKEN")
if oauth_token is None or oauth_token == "":
    pytest.skip("HF_TOKEN not set, skipping HF-dependent tests", allow_module_level=True)


@pytest.mark.parametrize(
    "model_id, expected",
    [
        ("distilbert-base-uncased-finetuned-sst-2-english", True),  # Valid model
        ("Hate-speech-CNERG/dehatebert-mono-arabic", True),  # Default whitelisted model
    ],
)
def test_is_valid_model(model_id, expected):
    """Test if the model ID is valid."""
    assert model_validation.is_valid_model(model_id) == expected


@pytest.mark.parametrize(
    "model_id, expected_error, expected_error_key",
    [
        ("invalid-model-id", model_validation.InvalidModelError, "model_not_found"),
        ("", model_validation.InvalidModelError, "invalid_model_id"),
        (None, model_validation.InvalidModelError, "invalid_model_id"),
        (
            "Hate-speech-CNERG/dehatebert-mono-arabic",
            model_validation.InvalidModelError,
            "no_safetensors",
        ),
        ("lelapa/InkubaLM-0.4B", model_validation.InvalidModelError, "invalid_architecture"),
    ],
)
@pytest.mark.patch_settings({"HUGGING_FACE_MODELS_WHITELIST": []})
def test_is_valid_model_invalid(model_id, expected_error, expected_error_key, patch_settings):
    """Test if the model ID is invalid."""
    with pytest.raises(expected_error) as exc_info:
        model_validation.is_valid_model(model_id)

    assert exc_info.value.detail["error_key"] == expected_error_key


@pytest.mark.parametrize(
    "model_id, expected",
    [
        ("my-whitelisted-model", True),  # Whitelisted model
        ("my-other-model", True),  # Another whitelisted model
    ],
)
@pytest.mark.patch_settings(
    {"HUGGING_FACE_MODELS_WHITELIST": ["my-whitelisted-model", "my-other-model"]}
)
def test_is_valid_model_whitelisted(model_id, expected, patch_settings):
    """Test if the model ID is valid."""
    assert model_validation.is_valid_model(model_id) == expected
