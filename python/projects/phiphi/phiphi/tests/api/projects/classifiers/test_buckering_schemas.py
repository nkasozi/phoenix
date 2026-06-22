"""Test cases for Perspective API schema classes."""

import pytest
from pydantic import ValidationError

from phiphi.api.projects.classifiers import bucketing_schemas


def test_bucket_threshold_validation():
    """Test BucketThreshold validation."""
    bucket = bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5)
    assert bucket.name == "low"
    assert bucket.upper_threshold == 0.5

    # Invalid bucket (threshold out of range)
    with pytest.raises(
        ValidationError, match="Bucket threshold must be between 0.0 and 1.0 inclusive."
    ):
        bucketing_schemas.BucketThreshold(name="invalid", upper_threshold=1.5)


def test_bucketing_config_validation():
    """Test BucketingConfig validation."""
    config = bucketing_schemas.BucketingConfig(
        class_name="toxicity",
        buckets=[
            bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
            bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
        ],
    )
    assert config.class_name == "toxicity"
    assert len(config.buckets) == 2


def test_bucketing_config_non_increasing_thresholds():
    """Test BucketingConfig with non-increasing thresholds."""
    with pytest.raises(ValidationError, match="Bucket thresholds must be strictly increasing."):
        bucketing_schemas.BucketingConfig(
            class_name="toxicity",
            buckets=[
                bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high", upper_threshold=0.4),
            ],
        )


def test_bucketing_config_last_threshold_not_one():
    """Test BucketingConfig with last threshold not equal to 1.0."""
    with pytest.raises(ValidationError, match="The last bucket threshold must be 1.0."):
        bucketing_schemas.BucketingConfig(
            class_name="toxicity",
            buckets=[
                bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high", upper_threshold=0.9),
            ],
        )


def test_bucketing_config_empty_buckets():
    """Test BucketingConfig with empty buckets."""
    with pytest.raises(ValidationError, match="At least one bucket must be provided."):
        bucketing_schemas.BucketingConfig(
            class_name="toxicity",
            buckets=[],
        )


def test_bucketing_config_class_name():
    """Test BucketingConfig with a specific class name."""
    config = bucketing_schemas.BucketingConfig(
        class_name="toxicity",
        buckets=[
            bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
            bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
        ],
    )
    assert config.class_name == "toxicity"
    assert len(config.buckets) == 2
    assert config.buckets[0].name == "low"
    assert config.buckets[1].name == "high"


def test_bucketing_config_no_class_name_error():
    """Test BucketingConfig without a class name raises an error."""
    with pytest.raises(ValidationError, match="Field required"):
        bucketing_schemas.BucketingConfig(  # type: ignore[call-arg]
            buckets=[
                bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
            ],
        )
