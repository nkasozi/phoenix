"""Conftest."""

import json
from typing import Generator, Iterator

import pandas as pd
import pydantic_core
import pytest
from fastapi.testclient import TestClient
from prefect.logging import disable_run_logger
from prefect.testing.utilities import prefect_test_harness
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from phiphi import config, platform_db, utils
from phiphi.api import main
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils
from phiphi.seed import main as seed_main
from phiphi.seed import users as seed_users

if config.settings.SENTRY_DSN:
    raise ValueError("Do not run tests with SENTRY_DSN set or you will get errors in the DSN")


#  This fixture has to be used in all tests otherwise database queries will not be done on the
#  testing database (`settings.TESTING_SQLALCHEMY_DATABASE_URI`) but on the one configured for the
#  app (`settings.SQLALCHEMY_DATABASE_URI`).
@pytest.fixture(scope="session", autouse=True)
def test_app(session) -> Generator[main.FastAPI, None, None]:
    """Initialise the test app.

    Includes overriding the get_session dependency to use the session fixture. This is necessary to
    use the test sessions in the app.
    """

    def override_get_session():
        yield session

    main.app.dependency_overrides[platform_db.get_session] = override_get_session
    yield main.app


@pytest.fixture(scope="session")
def client(test_app) -> Generator[TestClient, None, None]:
    """Client for testing.

    This client is deprecated and should be replaced with `client_no_user`, `client_admin` or
    something like that.
    """
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="session")
def client_no_user(test_app) -> Generator[TestClient, None, None]:
    """Client that has no authenticated user.

    This is useful for testing endpoints that do not require authentication and should replace any
    users of the `client` fixture that do not require authentication.
    """
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="session")
def client_admin(test_app) -> Generator[TestClient, None, None]:
    """Client for testing authenticated with main admin user.

    Must be used with the `reseed_tables` fixture to ensure the admin user is in the database.

    The fixture will work with the header or cookie authentication depending on the settings and
    means that the tests will pass if `USE_COOKIE_AUTH` is set to `True` or `False`.
    """
    if config.settings.COOKIE_AUTH_NAME:
        cookies = {config.settings.COOKIE_AUTH_NAME: config.settings.FIRST_ADMIN_USER_EMAIL}
    else:
        cookies = None
    with TestClient(
        test_app,
        headers={config.settings.HEADER_AUTH_NAME: config.settings.FIRST_ADMIN_USER_EMAIL},
        cookies=cookies,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def client_user_1(test_app) -> Generator[TestClient, None, None]:
    """Client for testing authenticated with first non admin user.

    Must be used with the `reseed_tables` fixture to ensure the user is in the database.

    The fixture will work with the header or cookie authentication depending on the settings and
    means that the tests will pass if `USE_COOKIE_AUTH` is set to `True` or `False`.
    """
    user_email = seed_users.TEST_USER_1_CREATE.email
    if config.settings.COOKIE_AUTH_NAME:
        cookies = {config.settings.COOKIE_AUTH_NAME: user_email}
    else:
        cookies = None
    with TestClient(
        test_app,
        headers={config.settings.HEADER_AUTH_NAME: user_email},
        cookies=cookies,
    ) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def test_engine():
    """Create a test engine for the database."""
    if config.settings.TESTING_SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("Tests cannot be run as TESTING_SQLALCHEMY_DATABASE_URI is not set.")
    engine = create_engine(str(config.settings.TESTING_SQLALCHEMY_DATABASE_URI))
    return engine


@pytest.fixture(scope="session")
def session(test_engine) -> Generator[Session, None, None]:
    """Create the session for testing."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="session")
def session_context(session) -> Generator[Session, None, None]:
    """Create the session for testing.

    This should be used when testing data pipelines that use
    `with platform_db.get_session_context() as session:`

    !!! Makes sure you are using `platform_db.get_session_context()` in your code and not
    `get_session_context` other wise the patch will not work.

    Recommended to use in conjunction with the `recreate_tables` or `reseed_tables` fixtures.
    """
    old_get_session_context = platform_db.get_session_context
    platform_db.get_session_context = lambda: session
    yield session
    platform_db.get_session_context = old_get_session_context


@pytest.fixture(scope="function")
def recreate_tables(session):
    """Recreate tables deleting all the data in the database.

    Use this fixture to reset the data for a test.
    """
    platform_db.Base.metadata.drop_all(bind=session.get_bind())
    platform_db.Base.metadata.create_all(bind=session.get_bind())
    yield session
    # Need to close the session or will not release the lock on the database
    # and next command in an other connection will hang.
    session.close()


@pytest.fixture(scope="function")
def reseed_tables(session):
    """Reseed the tables.

    Use this fixture to reset the data for a test.
    """
    try:
        seed_main.main(session, True)
        yield session
    finally:
        # Need to close the session or will not release the lock on the database
        # and next command in an other connection will hang.
        session.close()


@pytest.fixture(scope="function")
def patch_settings(request: pytest.FixtureRequest) -> Iterator[config.Settings]:
    """Patch the settings with given variables.

    Use this fixture to patch config.settings with the different values. The values are passed
    as a dictionary in the patch_settings decorator. Any settings that are not set via the
    dictionary will be set to the default value.

    Taken from:
    https://rednafi.com/python/patch_pydantic_settings_in_pytest/

    There where a few changes to the original code to make it work with the linting and versions in
    this project.

    Example:
    @pytest.mark.patch_settings(
        {"USE_COOKIE_AUTH": False, "COOKIE_AUTH_NAME": COOKIE_AUTH_TEST_NAME}
    )
    def test_something(patch_settings):
        pass
    """
    # Make a copy of the original settings
    original_settings = config.settings.model_copy()

    # Collect the values to patch
    marker = request.node.get_closest_marker("patch_settings")
    if marker is None:
        env_vars_to_patch = {}
    else:
        env_vars_to_patch = marker.args[0]

    # Patch the settings to use the default values
    for k, v in config.settings.model_fields.items():
        if v.default is not pydantic_core.PydanticUndefined:
            setattr(config.settings, k, v.default)

    for key, val in env_vars_to_patch.items():
        # Raise an error if the patch settings is not defined in the settings
        if not hasattr(config.settings, key):
            raise ValueError(f"Unknown setting: {key}")

        setattr(config.settings, key, val)

    # Reapply the validation of the settings
    # So that the parsing of the values in to fields is done correctly
    config.settings = config.Settings(**config.settings.model_dump())

    yield config.settings
    # Restore the original settings
    config.settings.__dict__.update(original_settings.__dict__)


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """Fixture to run prefect tests without api keys."""
    with prefect_test_harness():
        with disable_run_logger():
            yield


@pytest.fixture
def pipeline_jobs_sample_generalised_post_authors() -> pd.DataFrame:
    """Sample generalised post authors.

    Needed as a top level fixture so that it can be used in tests in the
    `phiphi.tests.pipeline_jobs` package and `phiphi.tests.api`.
    """
    path = utils.get_pipeline_sample_data_path("generalised_post_authors.json")
    with open(path, "r") as f:
        sample_authors = json.load(f)

    result_df = pd.DataFrame(sample_authors)
    result_df["phoenix_processed_at"] = pipeline_jobs_utils.col_to_utc_ms(
        result_df["phoenix_processed_at"]
    )
    return result_df
