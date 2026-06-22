"""Cookie Authorization test."""

from typing import Generator

import fastapi
import pytest
from fastapi.testclient import TestClient

from phiphi import config
from phiphi.api import deps, main
from phiphi.seed import users as seed_users

COOKIE_AUTH_TEST_NAME = "test_cookie_auth"


@pytest.fixture(scope="session")
def test_app_with_cookie(session, test_app) -> Generator[main.FastAPI, None, None]:
    """Initialise the test app.

    Includes overriding the email_cookie_scheme dependency to use the session fixture. So we can
    use the cookie authorization in the tests. This is needed because if the
    settings.USE_COOKIE_AUTH is False then email_cookie_scheme is a noop function.
    """
    email_cookie_scheme_override = fastapi.security.APIKeyCookie(
        name=COOKIE_AUTH_TEST_NAME, auto_error=False
    )

    main.app.dependency_overrides[deps.email_cookie_scheme] = email_cookie_scheme_override
    yield main.app
    # Reset the dependency override because I am scared that this could be run in a production
    # environment and the override could be left in place.
    main.app.dependency_overrides[deps.email_cookie_scheme] = deps.email_cookie_scheme


@pytest.fixture(scope="session")
def client_cookie_test_user_1(test_app_with_cookie) -> Generator[TestClient, None, None]:
    """Client for testing authenticated with test user 1."""
    with TestClient(
        test_app_with_cookie,
        cookies={COOKIE_AUTH_TEST_NAME: seed_users.TEST_USER_1_CREATE.email},
    ) as client:
        yield client


@pytest.fixture(scope="session")
def client_header_and_cookie(test_app_with_cookie) -> Generator[TestClient, None, None]:
    """Client for testing authenticated with header and cookie."""
    with TestClient(
        test_app_with_cookie,
        cookies={COOKIE_AUTH_TEST_NAME: seed_users.TEST_USER_1_CREATE.email},
        headers={config.settings.HEADER_AUTH_NAME: config.settings.FIRST_ADMIN_USER_EMAIL},
    ) as client:
        yield client


@pytest.mark.patch_settings({"USE_COOKIE_AUTH": False, "COOKIE_AUTH_NAME": COOKIE_AUTH_TEST_NAME})
def test_read_me_cookie_client_not_working(
    client_cookie_test_user_1: TestClient, reseed_tables, patch_settings
) -> None:
    """Test authorization users/me with a cookie but when settings for cookie is false."""
    response = client_cookie_test_user_1.get("/users/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Cannot authenticate."}


@pytest.mark.patch_settings({"USE_COOKIE_AUTH": True, "COOKIE_AUTH_NAME": COOKIE_AUTH_TEST_NAME})
def test_read_me_header_client_not_working(
    client_header_and_cookie: TestClient, reseed_tables, patch_settings
) -> None:
    """Test authorization users/me with a header and cookie.

    The header should take precedence over cookie.
    """
    response = client_header_and_cookie.get("/users/me")
    assert response.status_code == 200
    user = response.json()

    assert user["email"] == config.settings.FIRST_ADMIN_USER_EMAIL
    assert user["display_name"] == config.settings.FIRST_ADMIN_USER_DISPLAY_NAME


@pytest.mark.patch_settings({"USE_COOKIE_AUTH": True, "COOKIE_AUTH_NAME": COOKIE_AUTH_TEST_NAME})
def test_read_me_cookie_client(
    client_cookie_test_user_1: TestClient, reseed_tables, patch_settings
) -> None:
    """Test authorization users/me with a cookie but when settings for cookie is true."""
    response = client_cookie_test_user_1.get("/users/me")
    assert response.status_code == 200
    user = response.json()

    assert user["email"] == seed_users.TEST_USER_1_CREATE.email
    assert user["display_name"] == seed_users.TEST_USER_1_CREATE.display_name
