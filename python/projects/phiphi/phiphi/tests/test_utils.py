"""Test utils."""

import pytest

from phiphi import utils

MAIN_APIFY_API_KEY = "main_apify_key"
OTHER_APIFY_API_KEY = "other_apify_key"
OTHER_WORKSPACE_SLUG = "other_workspace_slug"
APIFY_API_KEYS_STR_1 = f'{{"main_workspace_slug": "{MAIN_APIFY_API_KEY}", "{OTHER_WORKSPACE_SLUG}": "{OTHER_APIFY_API_KEY}"}}'  # noqa: E501
SETTINGS_WORKSPACE_MAIN = {
    "APIFY_API_KEYS": APIFY_API_KEYS_STR_1,
    "FIRST_WORKSPACE_SLUG": "main_workspace_slug",
}
SETTINGS_WORKSPACE_OTHER = {
    "APIFY_API_KEYS": APIFY_API_KEYS_STR_1,
    "FIRST_WORKSPACE_SLUG": OTHER_WORKSPACE_SLUG,
}
DANEK_API_TOKENS_NESTED = {
    "main_workspace_slug": {
        "api_1": "token_1",
        "api_2": "token_2",
    },
    OTHER_WORKSPACE_SLUG: {
        "api_1": "other_token_1",
    },
}

DANEK_API_TOKENS_STR = {
    "main_workspace_slug": "legacy_token",
    OTHER_WORKSPACE_SLUG: "other_legacy_token",
}


@pytest.mark.patch_settings(SETTINGS_WORKSPACE_MAIN)
def test_get_apify_keys_main(patch_settings):
    """Test get apify keys."""
    assert utils.get_apify_api_key() == MAIN_APIFY_API_KEY


@pytest.mark.patch_settings(SETTINGS_WORKSPACE_MAIN)
def test_get_apify_keys_other(patch_settings):
    """Test get apify keys for other workspace."""
    assert utils.get_apify_api_key(OTHER_WORKSPACE_SLUG) == OTHER_APIFY_API_KEY


@pytest.mark.patch_settings(SETTINGS_WORKSPACE_OTHER)
def test_get_apify_keys_other_workspace(patch_settings):
    """Test get apify keys."""
    assert utils.get_apify_api_key() == OTHER_APIFY_API_KEY


@pytest.mark.patch_settings(SETTINGS_WORKSPACE_MAIN)
def test_get_apify_keys_not_found(patch_settings):
    """Test get apify keys."""
    with pytest.raises(ValueError):
        utils.get_apify_api_key("not_found")


@pytest.mark.patch_settings(
    {"APIFY_API_KEYS": APIFY_API_KEYS_STR_1, "FIRST_WORKSPACE_SLUG": "not_found"}
)
def test_get_apify_keys_not_found_workspace(patch_settings):
    """Test get apify keys."""
    with pytest.raises(ValueError):
        utils.get_apify_api_key()


def test_get_project_namespace():
    """Test get project namespace."""
    assert utils.get_project_namespace(1) == "project_id1"


def test_get_project_namespace_prefix():
    """Test get project namespace."""
    assert utils.get_project_namespace(1, "test_") == "test_project_id1"


@pytest.mark.parametrize(
    "project_id, namespace_prefix",
    [
        (-1, ""),
        (1, "test-"),
    ],
)
def test_get_project_namespace_invalid(project_id, namespace_prefix):
    """Test get project namespace."""
    with pytest.raises(ValueError):
        utils.get_project_namespace(project_id, namespace_prefix)


@pytest.mark.patch_settings(
    {
        "DANEK_API_TOKENS": DANEK_API_TOKENS_NESTED,
        "FIRST_WORKSPACE_SLUG": "main_workspace_slug",
    }
)
def test_get_danek_api_token_default_workspace_nested(patch_settings):
    """Test getting Danek API token using default workspace (nested structure)."""
    assert utils.get_danek_api_token("api_1") == "token_1"


@pytest.mark.patch_settings(
    {
        "DANEK_API_TOKENS": DANEK_API_TOKENS_NESTED,
        "FIRST_WORKSPACE_SLUG": "main_workspace_slug",
    }
)
def test_get_danek_api_token_other_workspace_nested(patch_settings):
    """Test getting Danek API token for a specific workspace (nested structure)."""
    assert utils.get_danek_api_token("api_1", OTHER_WORKSPACE_SLUG) == "other_token_1"


@pytest.mark.patch_settings(
    {
        "DANEK_API_TOKENS": DANEK_API_TOKENS_STR,
        "FIRST_WORKSPACE_SLUG": "main_workspace_slug",
    }
)
def test_get_danek_api_token_legacy_structure(patch_settings):
    """Test backwards compatibility when tokens are stored as strings."""
    assert utils.get_danek_api_token("any_api") == "legacy_token"


@pytest.mark.patch_settings(
    {
        "DANEK_API_TOKENS": DANEK_API_TOKENS_NESTED,
        "FIRST_WORKSPACE_SLUG": "main_workspace_slug",
    }
)
def test_get_danek_api_token_api_not_found(patch_settings):
    """Test error when API name is not found."""
    with pytest.raises(ValueError):
        utils.get_danek_api_token("nonexistent_api")


@pytest.mark.patch_settings(
    {
        "DANEK_API_TOKENS": DANEK_API_TOKENS_NESTED,
        "FIRST_WORKSPACE_SLUG": "main_workspace_slug",
    }
)
def test_get_danek_api_token_workspace_not_found(patch_settings):
    """Test error when workspace is not found."""
    with pytest.raises(ValueError):
        utils.get_danek_api_token("api_1", "nonexistent_workspace")
