"""Hugging Face classifier schema.

Note, still to implement is the threshold bucketings.
"""

from typing import Annotated, Literal, Optional

import pydantic
from typing_extensions import Self

from phiphi.api.projects.classifiers import base_schemas, bucketing_schemas


def default_bucketing_configs_factory() -> list[bucketing_schemas.BucketingConfig]:
    """Factory function to create the default bucketing config."""
    return [
        bucketing_schemas.BucketingConfig(
            class_name="*",
            buckets=[
                bucketing_schemas.BucketThreshold(name="low_prob", upper_threshold=0.25),
                bucketing_schemas.BucketThreshold(name="medium_prob", upper_threshold=0.5),
                bucketing_schemas.BucketThreshold(name="high_prob", upper_threshold=0.75),
                bucketing_schemas.BucketThreshold(name="very_high_prob", upper_threshold=1.0),
            ],
        )
    ]


class HuggingFaceParams(pydantic.BaseModel):
    """Runtime parameters for a Hugging Face classifier version."""

    model_id: Annotated[
        str,
        pydantic.Field(
            description=(
                "The identifier of the model on the Hugging Face Hub, e.g. "
                "'distilbert-base-uncased-finetuned-sst-2-english'."
            )
        ),
    ]
    bucketing_configs: list[bucketing_schemas.BucketingConfig] = pydantic.Field(
        default_factory=default_bucketing_configs_factory,
        description=(
            """Optional bucketing configurations for classifying scalar predictions into
            discrete classes. If provided, each class that the Hugging Face model emits
            needs to have a corresponding bucketing config defined here.
            If not provided, will use default bucketing config for all classes.
            Can't mix the default catch all "*" with configs for specific class names.
            """
        ),
    )

    @pydantic.model_validator(mode="after")
    def _no_mixed_catch_all(self) -> Self:
        """Ensure you don't have a '*' config alongside other class-specific configs."""
        names = {cfg.class_name for cfg in self.bucketing_configs}
        if "*" in names and len(names) > 1:
            raise ValueError(
                "Cannot mix catch-all '*' bucketing config with specific class configs."
            )
        return self


class HuggingFaceVersionBase(base_schemas.ClassifierSimpleVersionBase):
    """Version metadata for a Hugging Face classifier."""

    classes: list[base_schemas.ClassLabel] = pydantic.Field(
        default_factory=list,
        description=(
            "All class labels this model can emit. These must be provided "
            "explicitly; they are not auto-generated."
        ),
    )
    params: HuggingFaceParams

    @classmethod
    def format_class_name(cls, bucket_name: str, class_name: str) -> str:
        """Format a consistent class name from a bucket and class name.

        Args:
            bucket_name (str): The bucket name.
            class_name (str): The class name.

        Returns:
            str: A formatted class name (e.g., 'low_toxicity').
        """
        return f"{bucket_name}_{class_name}"

    @pydantic.model_validator(mode="after")
    def generate_classes(self) -> Self:
        """Generate classes based on bucket configs."""
        new_classes = []
        # Iterate over each bucket config
        for bucket_config in self.params.bucketing_configs:
            # For each bucket, create a ClassLabel
            for bucket in bucket_config.buckets:
                class_name = self.format_class_name(bucket.name, bucket_config.class_name)
                class_description = (
                    f"Score bucket '{bucket.name}' for class '{bucket_config.class_name}'"
                )
                new_classes.append(
                    base_schemas.ClassLabel(name=class_name, description=class_description)
                )
        self.classes = new_classes
        return self


class HuggingFaceVersionResponse(HuggingFaceVersionBase, base_schemas.ClassifierVersionResponse):
    """Response model for a Hugging Face classifier version."""


class HuggingFaceClassifierCreate(base_schemas.ClassifierCreateWithVersion):
    """Payload for creating a new Hugging Face classifier (with initial version)."""

    latest_version: HuggingFaceVersionBase


class HuggingFaceClassifierResponse(base_schemas.ClassifierResponseBase):
    """Lightweight view of a Hugging Face classifier."""

    type: Literal[base_schemas.ClassifierType.hugging_face]
    latest_version: Optional[HuggingFaceVersionResponse] = None


class HuggingFaceClassifierDetail(
    HuggingFaceClassifierResponse, base_schemas.ClassifierDetailBase
):
    """Full detail view of a Hugging Face classifier (includes metadata, history, etc.)."""


class HuggingFaceClassifierPipeline(
    HuggingFaceClassifierResponse, base_schemas.ClassifierPipelineBase
):
    """Version-guaranteed schema used when the pipeline needs the classifier in-memory."""

    latest_version: HuggingFaceVersionResponse
