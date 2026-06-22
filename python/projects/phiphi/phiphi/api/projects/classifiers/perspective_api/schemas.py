"""Perspective API classifier schemas."""

from enum import Enum
from typing import Literal, Optional

import pydantic
from typing_extensions import Self

from phiphi.api.projects.classifiers import base_schemas, bucketing_schemas


class PerspectiveAttribute(str, Enum):
    """Enum of Perspective API attributes."""

    toxicity = "toxicity"
    severe_toxicity = "severe_toxicity"
    identity_attack = "identity_attack"
    insult = "insult"
    threat = "threat"
    sexually_explicit = "sexually_explicit"
    flirtation = "flirtation"


class PerspectiveAttributeConfig(pydantic.BaseModel):
    """Configuration for a single Perspective attribute.

    For info on relevant threshold values, see Perspective API documentation:
    https://developers.perspectiveapi.com/s/about-the-api-score
    """

    enabled: bool = False
    buckets: list[bucketing_schemas.BucketThreshold] = [
        bucketing_schemas.BucketThreshold(name="low_prob", upper_threshold=0.25),
        bucketing_schemas.BucketThreshold(name="medium_prob", upper_threshold=0.5),
        bucketing_schemas.BucketThreshold(name="high_prob", upper_threshold=0.75),
        bucketing_schemas.BucketThreshold(name="very_high_prob", upper_threshold=1.0),
    ]

    @pydantic.model_validator(mode="after")
    def validate_buckets(self) -> Self:
        """Validate buckets only if enabled."""
        if self.enabled:
            if not self.buckets:
                raise ValueError("If enabled=True, at least one bucket must be provided.")
            thresholds = [b.upper_threshold for b in self.buckets]
            # Check strictly increasing thresholds
            if any(t2 <= t1 for t1, t2 in zip(thresholds, thresholds[1:])):
                raise ValueError("Bucket thresholds must be strictly increasing.")
            # Ensure last bucket threshold == 1.0
            if thresholds[-1] != 1.0:
                raise ValueError("The last bucket threshold must be 1.0.")
        return self


class PerspectiveAPIParams(pydantic.BaseModel):
    """Parameters for the Perspective API classifier.

    Each attribute is defined by its own config.
    """

    toxicity: PerspectiveAttributeConfig = PerspectiveAttributeConfig()
    severe_toxicity: PerspectiveAttributeConfig = PerspectiveAttributeConfig()
    identity_attack: PerspectiveAttributeConfig = PerspectiveAttributeConfig()
    insult: PerspectiveAttributeConfig = PerspectiveAttributeConfig()
    threat: PerspectiveAttributeConfig = PerspectiveAttributeConfig()
    sexually_explicit: PerspectiveAttributeConfig = PerspectiveAttributeConfig()
    flirtation: PerspectiveAttributeConfig = PerspectiveAttributeConfig()

    @pydantic.model_validator(mode="after")
    def validate_at_least_one_attribute(self) -> Self:
        """Ensure at least one attribute is enabled."""
        attrs = [
            self.toxicity,
            self.severe_toxicity,
            self.identity_attack,
            self.insult,
            self.threat,
            self.sexually_explicit,
            self.flirtation,
        ]
        if not any(attr.enabled for attr in attrs):
            raise ValueError("At least one Perspective attribute must be enabled.")
        return self


class PerspectiveAPIVersionBase(base_schemas.ClassifierSimpleVersionBase):
    """Perspective API version base schema."""

    # Classes will be generated automatically from params
    classes: list[base_schemas.ClassLabel] = []
    params: PerspectiveAPIParams

    @classmethod
    def format_class_name(cls, bucket_name: str, attribute_name: str) -> str:
        """Format a consistent class name from a bucket and attribute.

        Args:
            bucket_name (str): The bucket name.
            attribute_name (str): The attribute name.

        Returns:
            str: A formatted class name (e.g., 'low_toxicity').
        """
        return f"{bucket_name}_{attribute_name}"

    @pydantic.model_validator(mode="after")
    def generate_classes(self) -> Self:
        """Generate classes based on enabled attributes and their buckets."""
        new_classes = []
        # Iterate over each attribute in params
        for attribute_name, attribute_config in iter(self.params):
            if attribute_config.enabled:
                # For each bucket, create a ClassLabel
                for bucket in attribute_config.buckets:
                    class_name = self.format_class_name(bucket.name, attribute_name)
                    class_description = (
                        f"Score bucket '{bucket.name}' for attribute '{attribute_name}'"
                    )
                    new_classes.append(
                        base_schemas.ClassLabel(name=class_name, description=class_description)
                    )
        self.classes = new_classes
        return self


class PerspectiveAPIVersionResponse(
    PerspectiveAPIVersionBase, base_schemas.ClassifierVersionResponse
):
    """Perspective API version response schema."""


class PerspectiveAPIClassifierCreate(base_schemas.ClassifierCreateWithVersion):
    """Perspective API classifier create schema."""

    latest_version: PerspectiveAPIVersionBase


class PerspectiveAPIClassifierResponse(base_schemas.ClassifierResponseBase):
    """Perspective API classifier response."""

    type: Literal[base_schemas.ClassifierType.perspective_api]
    latest_version: Optional[PerspectiveAPIVersionResponse] = None


class PerspectiveAPIClassifierDetail(
    PerspectiveAPIClassifierResponse, base_schemas.ClassifierDetailBase
):
    """Perspective API classifier detail response."""

    # inherits fields from ClassifierDetailBase
    pass


class PerspectiveAPIClassifierPipeline(
    PerspectiveAPIClassifierResponse, base_schemas.ClassifierPipelineBase
):
    """Perspective API classifier pipeline response."""

    latest_version: PerspectiveAPIVersionResponse
