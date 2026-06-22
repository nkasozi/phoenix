"""Test cases for Perspective API schema classes."""

import pytest
from pydantic import ValidationError

from phiphi.api.projects.classifiers import bucketing_schemas
from phiphi.api.projects.classifiers.perspective_api import schemas


def test_perspective_attribute_config_validation():
    """Test PerspectiveAttributeConfig validation."""
    # Valid configuration
    config = schemas.PerspectiveAttributeConfig(
        enabled=True,
        buckets=[
            bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
            bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
        ],
    )
    assert config.enabled is True
    assert len(config.buckets) == 2

    # Invalid configuration (non-increasing thresholds)
    with pytest.raises(ValidationError, match="Bucket thresholds must be strictly increasing."):
        schemas.PerspectiveAttributeConfig(
            enabled=True,
            buckets=[
                bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high", upper_threshold=0.4),
            ],
        )

    # Invalid configuration (no buckets when enabled=True)
    with pytest.raises(
        ValidationError, match="If enabled=True, at least one bucket must be provided."
    ):
        schemas.PerspectiveAttributeConfig(enabled=True, buckets=[])

    # Invalid configuration (last bucket threshold != 1.0)
    with pytest.raises(ValidationError, match="The last bucket threshold must be 1.0."):
        schemas.PerspectiveAttributeConfig(
            enabled=True,
            buckets=[
                bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high", upper_threshold=0.9),
            ],
        )


def test_perspective_api_params_validation():
    """Test PerspectiveAPIParams validation."""
    # Valid params
    params = schemas.PerspectiveAPIParams(
        toxicity=schemas.PerspectiveAttributeConfig(
            enabled=True,
            buckets=[bucketing_schemas.BucketThreshold(name="low", upper_threshold=1.0)],
        )
    )
    assert params.toxicity.enabled is True

    # Invalid params (no attributes enabled)
    with pytest.raises(
        ValidationError, match="At least one Perspective attribute must be enabled."
    ):
        schemas.PerspectiveAPIParams()


def test_format_class_name():
    """Test formatting logic for class names."""
    # Test formatting logic for class names
    class_name = schemas.PerspectiveAPIVersionBase.format_class_name(
        bucket_name="low", attribute_name="toxicity"
    )
    assert class_name == "low_toxicity"


def test_generate_classes():
    """Test class name generation logic."""
    params = schemas.PerspectiveAPIParams(
        toxicity=schemas.PerspectiveAttributeConfig(
            enabled=True,
            buckets=[
                bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
            ],
        )
    )
    version_base = schemas.PerspectiveAPIVersionBase(params=params)

    assert len(version_base.classes) == 2
    assert version_base.classes[0].name == "low_toxicity"
    assert version_base.classes[1].name == "high_toxicity"
