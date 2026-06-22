"""Constants for phiphi."""

from enum import StrEnum

DEFAULT_IMAGE_REPO = "registry.gitlab.com/howtobuildup/phoenix/python/phiphi"
DEFAULT_IMAGE = f"{DEFAULT_IMAGE_REPO}:latest"


class WorkPool(StrEnum):
    """Work pool enum."""

    main = "main-work-pool"
