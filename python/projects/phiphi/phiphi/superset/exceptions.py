"""Superset-specific exceptions."""


class SupersetError(Exception):
    """Base Superset exception."""


class SupersetConnectionError(SupersetError):
    """Superset service unavailable."""


class SupersetAPIError(SupersetError):
    """API request failed."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize SupersetAPIError.

        Args:
            message: Error message.
            status_code: HTTP status code if available.
        """
        super().__init__(message)
        self.status_code = status_code


class SupersetTimeoutError(SupersetError):
    """Superset request timed out."""
