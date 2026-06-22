"""Phiphi API custom exception."""

import fastapi


class HttpException400(fastapi.HTTPException):
    """Custom exception for 400 status code."""

    def __init__(self, detail: str) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=400, detail=detail)


class HttpException404(fastapi.HTTPException):
    """Custom exception for 404 status code."""

    def __init__(self, detail: str) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=404, detail=detail)


class Forbidden(fastapi.HTTPException):
    """Custom exception for 403 status code."""

    def __init__(self, detail: str) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=403, detail=detail)


class UnknownIntegrityError(fastapi.HTTPException):
    """Custom exception for unknown integrity error."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        # Important that no SQL are in the detail string as this could lead to a security risk
        super().__init__(status_code=500, detail="Internal server error")


class ProjectNotFound(fastapi.HTTPException):
    """Custom exception for null projects."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=404, detail="Project not found")


class WorkspaceNotFound(fastapi.HTTPException):
    """Custom exception for null workspace."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=400, detail="Workspace not found")


class GatherNotFound(fastapi.HTTPException):
    """Custom exception for null gather."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=400, detail="Gather not found")


class ForeignObjectHasActiveJobRun(fastapi.HTTPException):
    """Custom exception for active job run on foreign object."""

    def __init__(self, foreign_id: int, foreign_job_type: str) -> None:
        """Constructor for custom exception."""
        super().__init__(
            status_code=400,
            detail=(
                f"Foreign object has an active job run. Type: {foreign_job_type}, Id: {foreign_id}"
            ),
        )


class ClassifierNotFound(fastapi.HTTPException):
    """Custom exception for null classifier."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=404, detail="Classifier not found")


class ClassifierArchived(fastapi.HTTPException):
    """Custom exception for archived classifiers."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=400, detail="Classifier is archived.")


class IntermediatoryClassNotFound(fastapi.HTTPException):
    """Custom exception for null Class."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=404, detail="Intermediatory Class not found")


class IntermediatoryClassNameConflict(fastapi.HTTPException):
    """Custom exception for null Class."""

    def __init__(self) -> None:
        """Constructor for custom exception."""
        super().__init__(status_code=400, detail="Intermediatory Class with name already exists")


class ProjectResourcesNotProvisioned(fastapi.HTTPException):
    """Raised when attempting to run a job on a project that hasn't finished provisioning."""

    def __init__(self, project_id: int) -> None:
        """Constructor for custom exception."""
        super().__init__(
            status_code=409,
            detail=(
                f"Project {project_id} resources are still being provisioned. "
                "Please wait a few minutes and try again."
            ),
        )
