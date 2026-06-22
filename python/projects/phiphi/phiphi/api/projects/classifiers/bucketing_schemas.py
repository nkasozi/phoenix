"""Schemas for bucketing scalar predictions into classes."""

from typing import Annotated, Self

import pydantic


class BucketThreshold(pydantic.BaseModel):
    """A bucket and threshold; defining a classification tier for a scalar class prediction.

    A series of BucketThresholds define the classification tiers for a given scalar class
    prediction.
    """

    name: str
    upper_threshold: Annotated[
        float, pydantic.Field(description="Score threshold between 0.0 and 1.0 inclusive.")
    ]

    @pydantic.model_validator(mode="after")
    def validate_threshold_range(self) -> Self:
        """Validate threshold is between 0.0 and 1.0 inclusive."""
        if not (0.0 <= self.upper_threshold <= 1.0):
            raise ValueError("Bucket threshold must be between 0.0 and 1.0 inclusive.")
        return self


class BucketingConfig(pydantic.BaseModel):
    """Configuration for bucketing scalar predictions into discreet classes."""

    class_name: str = pydantic.Field(
        description="Class name of the scalar prediction to bucket..",
    )
    buckets: list[BucketThreshold] = pydantic.Field(
        default_factory=list, description="List of bucket thresholds."
    )

    @pydantic.model_validator(mode="after")
    def validate_buckets(self) -> Self:
        """Validate buckets only if enabled."""
        if not self.buckets:
            raise ValueError("At least one bucket must be provided.")
        thresholds = [b.upper_threshold for b in self.buckets]
        # Check strictly increasing thresholds
        if any(t2 <= t1 for t1, t2 in zip(thresholds, thresholds[1:])):
            raise ValueError("Bucket thresholds must be strictly increasing.")
        # Ensure last bucket threshold == 1.0
        if thresholds[-1] != 1.0:
            raise ValueError("The last bucket threshold must be 1.0.")
        return self
