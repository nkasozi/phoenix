"""Phoenix superset config."""

import os

from flask_appbuilder.security.manager import AUTH_REMOTE_USER  # type: ignore[import-untyped]
from phoenix_superset import custom_sso_manager

AUTH_TYPE = AUTH_REMOTE_USER

# Default of x-auth-request-email is what oauth2-proxy set up uses
AUTH_REMOTE_USER_ENV_VAR = os.getenv("AUTH_REMOTE_USER_ENV_VAR", "HTTP_X_AUTH_REQUEST_EMAIL")

# This is needed to test the system without the authentication layer
LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL")
AUTH_USER_REGISTRATION = True

# Enables the FAB Security REST API
# - required for role/permission management via Superset API
# Will default to False, unless overridden by:
# - an env var in the container, or
# - config overrides in the helm chart.
FAB_ADD_SECURITY_API = os.getenv("FAB_ADD_SECURITY_API", "False").lower() in ("true", "1")

CUSTOM_SECURITY_MANAGER = custom_sso_manager.PhoenixCustomSSOSecurityManager

# DASHBOARD_RBAC is required so that roles can be seen and set on dashboards via the UI,
# and to make the dev environment closer to the configuration of production.
FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
}

# White label settings
APP_NAME = "Dashboard - Phoenix"
APP_ICON = "/static/assets/images/logo_buildup_short_200.png"
APP_ICON_WIDTH = 200
FAVICONS = [
    {
        "rel": "apple-touch-icon",
        "sizes": "180x180",
        "href": "/static/assets/images/apple-touch-icon.png",
    },
    {"rel": "icon", "sizes": "32x32", "href": "/static/assets/images/favicon-32x32.png"},
    {"rel": "icon", "sizes": "16x16", "href": "/static/assets/images/favicon-16x16.png"},
]
