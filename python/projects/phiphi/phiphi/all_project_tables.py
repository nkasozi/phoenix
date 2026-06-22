"""All Project db tables."""

from phiphi import project_db
from phiphi.pipeline_jobs import (
    classified_authors,  # noqa: F401
    classified_messages,  # noqa: F401
    classified_messages_errors,  # noqa: F401
    gather_batches,  # noqa: F401
    generalised_messages,  # noqa: F401
    tabulated_messages,  # noqa: F401
)

metadata = project_db.metadata
