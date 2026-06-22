"""Test config."""

import os
from unittest import mock

import dotenv
import pytest

from phiphi import config

TEST_ENV_FILE = "tests/test_config.environment"


# Need to clear the environment or the values will be overwritten in the envfile
@mock.patch.dict(os.environ, {}, clear=True)
def test_settings():
    """Test the settings."""
    expected_config = dotenv.dotenv_values(TEST_ENV_FILE)
    settings = config.Settings(_env_file=TEST_ENV_FILE)  # type: ignore [call-arg]

    assert str(settings.SQLALCHEMY_DATABASE_URI) == expected_config["SQLALCHEMY_DATABASE_URI"]


OVERRIDE = "sqlite:///overwrite.db"


@mock.patch.dict(os.environ, {"SQLALCHEMY_DATABASE_URI": OVERRIDE}, clear=True)
def test_settings_env_oerwride():
    """Test the settings."""
    expected_config = dotenv.dotenv_values(TEST_ENV_FILE)
    settings = config.Settings(_env_file=TEST_ENV_FILE)  # type: ignore [call-arg]

    assert str(settings.SQLALCHEMY_DATABASE_URI) != expected_config.get("SQLALCHEMY_DATABASE_URI")
    assert str(settings.SQLALCHEMY_DATABASE_URI) == OVERRIDE


@pytest.mark.patch_settings({"USE_COOKIE_AUTH": True, "COOKIE_AUTH_NAME": "test"})
def test_patch_settings(patch_settings):
    """Test patch settings fixture."""
    assert config.settings.USE_COOKIE_AUTH
    assert config.settings.COOKIE_AUTH_NAME == "test"
    # patch_settings sets all undefined to default values
    # so even if this is set differently in the env file, it will be reset here
    assert config.settings.HEADER_AUTH_NAME == "x-auth-request-email"


@pytest.mark.patch_settings({"USE_COOKIE_AUTH": False, "COOKIE_AUTH_NAME": "test2"})
def test_patch_settings_2(patch_settings):
    """Test patch settings fixture."""
    assert not config.settings.USE_COOKIE_AUTH
    assert config.settings.COOKIE_AUTH_NAME == "test2"
    # patch_settings sets all undefined to default values
    # so even if this is set differently in the env file, it will be reset here
    assert config.settings.HEADER_AUTH_NAME == "x-auth-request-email"
