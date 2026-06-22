"""Health check flows."""

import prefect

from hugging_face_classifier import utils


@prefect.task
def check_cuda() -> bool:
    """Check if CUDA is available."""
    return utils.is_cuda_available()


@prefect.flow(name="health_check_gpu")
def health_check_gpu() -> None:
    """Health check flow for GPU availability.

    This flow checks the health of the system by checking the connections to the database and
    external services.
    """
    logger = prefect.get_run_logger()
    logger.info("Starting health checks.")
    assert check_cuda(), "CUDA is not available."
    logger.info("Health checks completed.")
