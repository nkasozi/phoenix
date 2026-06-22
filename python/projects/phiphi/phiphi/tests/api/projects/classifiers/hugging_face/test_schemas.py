"""Test cases for Hugging Face classifier schema classes."""

import pytest

from phiphi.api.projects.classifiers import bucketing_schemas
from phiphi.api.projects.classifiers.hugging_face import schemas


def test_hugging_face_params_validation():
    """Test HuggingFaceParams validation."""
    # Valid params
    params = schemas.HuggingFaceParams(
        model_id="test-model",
        bucketing_configs=[
            bucketing_schemas.BucketingConfig(
                class_name="toxicity",
                buckets=[bucketing_schemas.BucketThreshold(name="low", upper_threshold=1.0)],
            )
        ],
    )
    assert params
    assert params.model_id == "test-model"
    assert len(params.bucketing_configs) == 1


def test_hugging_face_params_default():
    """Test default HuggingFaceParams."""
    default_params = schemas.HuggingFaceParams(model_id="default-model")
    assert default_params.model_id == "default-model"
    assert default_params.bucketing_configs is not None
    assert len(default_params.bucketing_configs) == 1
    assert default_params.bucketing_configs[0].class_name == "*"


def test_format_class_name():
    """Test formatting logic for class names."""
    # Test formatting logic for class names
    class_name = schemas.HuggingFaceVersionBase.format_class_name(
        bucket_name="low", class_name="toxicity"
    )
    assert class_name == "low_toxicity"


def test_generate_classes():
    """Test class name generation logic."""
    params = schemas.HuggingFaceParams(
        model_id="test-model",
        bucketing_configs=[
            bucketing_schemas.BucketingConfig(
                class_name="toxicity",
                buckets=[
                    bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                    bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                ],
            ),
            bucketing_schemas.BucketingConfig(
                class_name="aggression",
                buckets=[
                    bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                    bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                ],
            ),
        ],
    )
    version = schemas.HuggingFaceVersionBase(params=params)
    assert len(version.classes) == 4
    assert version.classes[0].name == "low_toxicity"
    assert version.classes[1].name == "high_toxicity"
    assert version.classes[2].name == "low_aggression"
    assert version.classes[3].name == "high_aggression"


def test_generate_classes_default():
    """Test class name generation logic."""
    default_params = schemas.HuggingFaceParams(model_id="default-model")
    version = schemas.HuggingFaceVersionBase(params=default_params)
    assert len(version.classes) == 4
    assert version.classes[0].name == "low_prob_*"
    assert version.classes[1].name == "medium_prob_*"
    assert version.classes[2].name == "high_prob_*"
    assert version.classes[3].name == "very_high_prob_*"


def test_hugging_face_params_rejects_mixed_catch_all():
    """Mixing '*' with any other bucketing_config should error."""
    with pytest.raises(ValueError, match="Cannot mix catch-all"):
        schemas.HuggingFaceParams(
            model_id="test-model",
            bucketing_configs=[
                # catch-all
                bucketing_schemas.BucketingConfig(
                    class_name="*",
                    buckets=[bucketing_schemas.BucketThreshold(name="low", upper_threshold=1.0)],
                ),
                # a specific config alongside it
                bucketing_schemas.BucketingConfig(
                    class_name="toxicity",
                    buckets=[bucketing_schemas.BucketThreshold(name="low", upper_threshold=1.0)],
                ),
            ],
        )
