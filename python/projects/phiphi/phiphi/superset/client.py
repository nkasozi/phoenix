"""Superset REST API client - session and authentication.

Superset requires session-based authentication with CSRF tokens:
1. Login via /login/ with X-Auth-Request-Email header to establish session cookie
2. Fetch CSRF token from /api/v1/security/csrf_token/
3. Include session cookie and X-CSRFToken header on mutating requests
"""

import logging
from typing import Any

import requests

from phiphi import config
from phiphi.superset import exceptions

logger = logging.getLogger(__name__)


def get_base_url() -> str | None:
    """Get Superset API base URL.

    Returns:
        Superset API base URL from config.
    """
    return config.settings.SUPERSET_API_URL


def handle_response(response: requests.Response, operation: str) -> dict[str, Any]:
    """Handle API response, raising appropriate exceptions.

    Args:
        response: Response from requests.
        operation: Description of the operation for error messages.

    Returns:
        Parsed JSON response.

    Raises:
        SupersetAPIError: If the response indicates an error.
    """
    try:
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.HTTPError as e:
        body = response.text[:500] if response.content else ""
        raise exceptions.SupersetAPIError(
            f"{operation} failed: {e} | response body: {body}", response.status_code
        )


def get_authenticated_session(
    base_url: str | None = None,
    service_account_email: str | None = None,
) -> requests.Session:
    """Create authenticated session with CSRF token.

    Args:
        service_account_email: Email for X-Auth-Request-Email header.
        base_url: Superset base URL.

    Returns:
        Authenticated requests.Session with CSRF token.

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If login or CSRF token fetch fails.
    """
    url = base_url or get_base_url()
    email = service_account_email or config.settings.SUPERSET_SERVICE_ACCOUNT_EMAIL

    session = requests.Session()
    session.headers["X-Auth-Request-Email"] = email

    try:
        login_response = session.get(f"{url}/login/", allow_redirects=True, timeout=30)
        if login_response.status_code != 200:
            raise exceptions.SupersetAPIError(
                f"Login failed: {login_response.status_code}", login_response.status_code
            )

        csrf_response = session.get(f"{url}/api/v1/security/csrf_token/", timeout=30)
        csrf_data = handle_response(csrf_response, "Get CSRF token")
        csrf_token = csrf_data.get("result")

        if not csrf_token:
            raise exceptions.SupersetAPIError("CSRF token not found")

        session.headers["X-CSRFToken"] = csrf_token
        return session

    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")


def health_check(base_url: str | None = None) -> bool:
    """Check if Superset is available.

    Args:
        base_url: Superset base URL.

    Returns:
        True if Superset is healthy, False otherwise.
    """
    url = base_url or get_base_url()
    try:
        response = requests.get(f"{url}/health", timeout=10)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
