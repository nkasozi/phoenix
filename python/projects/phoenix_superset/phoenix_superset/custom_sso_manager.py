"""Custom SSO Manager for Superset.

This module contains a custom SSO manager for Superset that allows for
authentication via a header in the request. This is useful for integrating Superset with an
existing authentication system such as the oauth2-proxy layer we use in Phoenix.

To use this custom SSO manager, set the following configuration in your
Superset configuration file:

```python
from custom_sso_manager import PhoenixCustomSSOSecurityManager

AUTH_TYPE = AUTH_REMOTE_USER
AUTH_REMOTE_USER_ENV_VAR = "x-auth-request-email"
# Will allow user self registration, allowing to create Flask users from Authorized User
AUTH_USER_REGISTRATION = True
# The default user self registration role
AUTH_USER_REGISTRATION_ROLE = "Admin"

CUSTOM_SECURITY_MANAGER = PhoenixCustomSSOSecurityManager
```

This will override the default Superset security manager with the custom SSO
manager defined in this module.

"""

import logging
from typing import Union

import werkzeug
from flask import current_app, g, redirect, request
from flask_appbuilder.const import (  # type: ignore[import-untyped]
    LOGMSG_WAR_SEC_LOGIN_FAILED,
)
from flask_appbuilder.security.sqla.models import User  # type: ignore[import-untyped]
from flask_appbuilder.security.views import AuthView  # type: ignore[import-untyped]
from flask_appbuilder.utils.base import get_safe_redirect  # type: ignore[import-untyped]
from flask_appbuilder.views import expose  # type: ignore[import-untyped]
from flask_login import current_user, login_user, logout_user  # type: ignore[import-untyped]
from superset.security import SupersetSecurityManager  # type: ignore[import-untyped]
from werkzeug.wrappers import Response as WerkzeugResponse

logger = logging.getLogger(__name__)


def sanitize_log_input(input_str: str) -> str:
    """Sanitize input to prevent log injection."""
    return input_str.replace("\r", "").replace("\n", "").replace("%0d", "").replace("%0a", "")


######
### Uncomment to see logs in the superset server output
# logger.setLevel(logging.DEBUG)


class NotAuthorised(werkzeug.exceptions.HTTPException):
    """Not Authorised Exception."""

    code = 401
    description = (
        "Not Authorized for this dashboard."
        " Please try to log in again. If you get really stuck, contact an admin."
    )


class AutheRemoteUserViewCustom(AuthView):  # type: ignore[no-any-unimported]
    """Custom view for remote user authentication.

    Based on:
    https://github.com/dpgaspar/Flask-AppBuilder/blob/master/flask_appbuilder/security/views.py#L729-L747
    """

    login_template = ""

    @expose("/login/")
    def login(self) -> WerkzeugResponse:
        """Login view for remote user authentication.

        If logged in will redirect to the next URL, if not will redirect to the
        login URL if configured, otherwise will raise an exception.
        """
        # Redirect it if has been configured
        email = self.appbuilder.sm.auth_remote_key
        header = self.appbuilder.sm.auth_remote_user_env_var
        logger.debug("Login View: Auth Header key: %s", header)
        logger.debug("Login View: Auth header value: %s", email)
        logger.debug(f"Login View: Current user: {current_user}")
        logger.debug(f"Login View: Current user: {g.user}")
        sanitized_headers = str(request.headers).replace("\r\n", "").replace("\n", "")
        logger.debug(f"Login View: headers {sanitized_headers}")
        if g.user is not None and g.user.is_authenticated and g.user.email == email:
            next_url = request.args.get("next", "")
            return redirect(get_safe_redirect(next_url))
        login_url = self.appbuilder.app.config.get("LOGIN_REDIRECT_URL")
        logger.debug("Login View: Login URL: %s", login_url)
        if email:
            user = self.appbuilder.sm.auth_user_remote_user(email)
            if user:
                login_user(user)
                next_url = request.args.get("next", "")
                return redirect(get_safe_redirect(next_url))
            if not user:
                if "text/html" in request.accept_mimetypes:
                    # For some stupid reason render_template has type Any rather then response?
                    return self.render_template("401.html", login_url=login_url)  # type: ignore[no-any-return]
                else:
                    raise NotAuthorised()

        if login_url:
            return redirect(login_url)

        # As a fallback 500 error as the system is not well configured
        raise Exception(
            f"The {header} header is not set and no login URL is set. "
            "Please configure the {header} header or set a login URL."
        )

    @expose("/auth_check/")
    def auth_check(self) -> WerkzeugResponse:
        """Auth check view for remote user authentication."""
        return WerkzeugResponse("OK")


# Permission-View mappings that should be blocked to prevent data export/download.
# These are removed from all roles to prevent CSV, Excel, and JSON downloads.
# Reference: https://github.com/apache/superset/discussions/30161
FORBIDDEN_DATA_EXPORT_PVMS: set[tuple[str, str]] = {
    ("can_csv", "Superset"),
    ("can_csv_download", "Superset"),
    ("can_export", "Chart"),
    ("can_export", "Dashboard"),
    ("can_export", "Dataset"),
    ("can_export", "ImportExportRestApi"),
    ("can_export_csv", "Chart"),
    ("can_view_chart_as_table", "Dashboard"),
}


class PhoenixCustomSSOSecurityManager(SupersetSecurityManager):  # type: ignore[no-any-unimported]
    """Custom SSO Security Manager for Superset.

    Based on:
    https://github.com/dpgaspar/Flask-AppBuilder/blob/master/flask_appbuilder/security/manager.py#L1340-L1368

    The auth_remote_user_env_var has been added as the flask_appbuilder version that superset is
    currently using does not have this functionality.

    This also blocks data export permissions (CSV, Excel, JSON downloads) for all users.
    """

    authremoteuserview = AutheRemoteUserViewCustom

    def can_access(self, permission_name: str, view_name: str) -> bool:
        """Check if user can access a permission-view combination.

        Overrides the base method to block data export permissions for all users.
        This prevents CSV, Excel, and JSON downloads from charts and dashboards.
        """
        if (permission_name, view_name) in FORBIDDEN_DATA_EXPORT_PVMS:
            logger.debug(
                "Blocked access to forbidden permission: %s on %s",
                permission_name,
                view_name,
            )
            return False
        return bool(super().can_access(permission_name, view_name))

    def __init__(self, appbuilder) -> None:  # type: ignore[no-untyped-def]
        """Create a custom SSO security manager.

        Taken from:
        https://github.com/dpgaspar/Flask-AppBuilder/blob/master/flask_appbuilder/security/manager.py#L261-L262
        """
        super().__init__(appbuilder)
        app = self.appbuilder.get_app
        app.config.setdefault("AUTH_REMOTE_USER_ENV_VAR", "REMOTE_USER")

    @property
    def auth_remote_user_env_var(self) -> str:
        """Get the remote user environment variable.

        Taken from:
        https://github.com/dpgaspar/Flask-AppBuilder/blob/master/flask_appbuilder/security/manager.py#L426-L428
        """
        return str(self.appbuilder.get_app.config["AUTH_REMOTE_USER_ENV_VAR"])

    @property
    def auth_remote_key(self) -> Union[str, None]:
        """Get the remote user key."""
        return request.environ.get(self.auth_remote_user_env_var)

    def auth_user_remote_user(self, email: str) -> Union[User, None]:  # type: ignore[no-any-unimported]
        """REMOTE_USER user Authentication.

        Custom version that uses the email to find the user rather than the username.
        """
        if not email:
            return None
        user = self.find_user(email=email)
        logger.debug("Found user:")
        logger.debug(user)

        # User does not exist, create one if auto user registration.
        if user is None and self.auth_user_registration:
            logger.debug(f"CREATING USER with email {email}")
            user = self.add_user(
                username=email,
                first_name="remote_user",
                last_name="-",
                email=email,
                role=self.find_role(self.auth_user_registration_role),
            )
        logging.debug("User: %s", user)

        if user is None:
            logger.info(LOGMSG_WAR_SEC_LOGIN_FAILED, email)
            return None

        if user and not user.is_active:
            logger.info(LOGMSG_WAR_SEC_LOGIN_FAILED, email)
            return None

        self.update_user_auth_stat(user)
        return user

    def load_user(self, pk: int) -> Union[User, None]:  # type: ignore[no-any-unimported]
        """Load user.

        Based on:
        https://github.com/dpgaspar/Flask-AppBuilder/blob/c65e067f09e741c00322221263c8599b8e8811d5/flask_appbuilder/security/manager.py#L2160C1-L2163C24

        But with the fix for if the users is not found.
        """
        user = self.get_user_by_id(int(pk))
        if not user:
            return None
        if user.is_active:
            return user

        return None

    @staticmethod
    def before_request():  # type: ignore[no-untyped-def]
        """Method called before each request.

        Based on:
        https://github.com/dpgaspar/Flask-AppBuilder/blob/c65e067f09e741c00322221263c8599b8e8811d5/flask_appbuilder/security/manager.py#L2173-L2175

        There is no unit test for this because setting up the superset for testing is quite
        challenging. It should be tested by hand :(.
        """
        logger.debug("Before request")
        sanitized_request = str(request).replace("\r\n", "").replace("\n", "")
        logger.debug(f"Request: {sanitized_request}")
        sanitized_environ = {
            sanitize_log_input(key): sanitize_log_input(str(value))
            for key, value in request.environ.items()
        }
        logger.debug(f"Request environment {sanitized_environ}")
        # Ignoring the attr-defined as appbuilder is an attribute of a flast app builder
        sm = current_app.appbuilder.sm  # type: ignore[attr-defined]
        email = sm.auth_remote_key
        logger.debug("Email to auth to: %s", email)
        logger.debug("Current user: %s", current_user)
        if current_user and current_user.is_authenticated and current_user.email != email:
            logger.debug("No match between header and current user email")
            logger.debug("Current user email: %s", current_user.email)
            logout_user()
            return redirect("/login/")
        else:
            logger.debug("Match between header and current user email")
            g.user = current_user
