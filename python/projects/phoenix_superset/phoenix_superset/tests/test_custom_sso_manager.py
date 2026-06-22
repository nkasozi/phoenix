"""Test PhoenixCustomSSOSecurityManager.

Based on:
https://github.com/dpgaspar/Flask-AppBuilder/blob/c65e067f09e741c00322221263c8599b8e8811d5/tests/security/test_auth_remote_user.py

"""

import unittest

from flask import Flask
from flask_appbuilder import SQLA, AppBuilder  # type: ignore[import-untyped]
from flask_appbuilder.const import AUTH_REMOTE_USER  # type: ignore[import-untyped]

from phoenix_superset import custom_sso_manager


class AuthRemoteUserTestCase(unittest.TestCase):
    """Test PhoenixCustomSSOSecurityManager."""

    def setUp(self):
        """Set up the test."""
        # start Flask
        self.app = Flask(__name__)
        self.app.config["AUTH_TYPE"] = AUTH_REMOTE_USER

        # start Database
        self.db = SQLA(self.app)

    def tearDown(self):
        """Tear down the test."""
        # Remove test user if appbuilder was created
        if hasattr(self, "appbuilder"):
            user_alice = self.appbuilder.sm.find_user("alice")
            if user_alice:
                self.db.session.delete(user_alice)
                self.db.session.commit()

            # stop Flask-AppBuilder
            delattr(self, "appbuilder")

        # stop Flask
        delattr(self, "app")

        # stop Database
        self.db.session.remove()
        delattr(self, "db")

    def create_appbuilder(self):
        """Create appbuilder."""
        return AppBuilder(
            self.app,
            self.db.session,
            security_manager_class=custom_sso_manager.PhoenixCustomSSOSecurityManager,
        )

    def test_unset_remote_user_env_var(self):
        """Test unset remote user env var."""
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        self.assertEqual(sm.auth_remote_user_env_var, "REMOTE_USER")

    def test_set_remote_user_env_var(self):
        """Test set remote user environment variable."""
        self.app.config["AUTH_REMOTE_USER_ENV_VAR"] = "HTTP_REMOTE_USER"
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        self.assertEqual(sm.auth_remote_user_env_var, "HTTP_REMOTE_USER")

    def test_normal_login(self):
        """Test normal login."""
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        # register a user
        _ = sm.add_user(
            username="alice",
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            role=[],
        )

        self.assertTrue(sm.auth_user_remote_user("alice@example.com"))

    def test_not_added_login(self):
        """Test a email that does not have a user."""
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        # register a user
        _ = sm.add_user(
            username="alice",
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            role=[],
        )

        self.assertFalse(sm.auth_user_remote_user("alice2@example.com"))

    def test_inactive_user_login(self):
        """Test inactive user login."""
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        # register a user
        alice_user = sm.add_user(
            username="alice",
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            role=[],
        )
        alice_user.active = False
        user = sm.auth_user_remote_user(alice_user.email)
        self.assertFalse(user)

    def test_create_user_login(self):
        """Test user is created if AUTH_USER_REGISTRATION is set."""
        self.app.config["AUTH_USER_REGISTRATION"] = True
        self.app.config["AUTH_USER_REGISTRATION_ROLE"] = "Admin"
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        # register a user
        email = "alice@example.com"
        user = sm.auth_user_remote_user(email)
        self.assertTrue(user)
        self.assertEqual(user.username, email)
        self.assertEqual(user.first_name, "remote_user")
        self.assertEqual(user.last_name, "-")
        self.assertEqual(user.email, email)
        self.assertEqual(str(user.roles), "[Admin]")

        alice_user = sm.find_user(email=email)
        self.assertTrue(alice_user)

    def test_forbidden_data_export_permissions_blocked(self):
        """Test that data export permissions are blocked for all users."""
        self.appbuilder = self.create_appbuilder()
        sm = self.appbuilder.sm

        # These permissions should always return False
        forbidden_permissions = [
            ("can_csv", "Superset"),
            ("can_csv_download", "Superset"),
            ("can_export", "Chart"),
            ("can_export", "Dashboard"),
            ("can_export", "Dataset"),
            ("can_export", "ImportExportRestApi"),
            ("can_export_csv", "Chart"),
            ("can_view_chart_as_table", "Dashboard"),
        ]

        for permission_name, view_name in forbidden_permissions:
            with self.subTest(permission=permission_name, view=view_name):
                self.assertFalse(
                    sm.can_access(permission_name, view_name),
                    f"Permission {permission_name} on {view_name} should be blocked",
                )

    def test_non_forbidden_permissions_not_in_blocklist(self):
        """Test that non-export permissions are not in the forbidden list."""
        from phoenix_superset.custom_sso_manager import FORBIDDEN_DATA_EXPORT_PVMS

        # These should not be in the forbidden list
        allowed_permissions = [
            ("can_read", "Chart"),
            ("can_read", "Dashboard"),
            ("can_write", "Chart"),
            ("can_list", "Dashboard"),
        ]

        for permission_name, view_name in allowed_permissions:
            with self.subTest(permission=permission_name, view=view_name):
                self.assertNotIn(
                    (permission_name, view_name),
                    FORBIDDEN_DATA_EXPORT_PVMS,
                    f"Permission {permission_name} on {view_name} should not be in forbidden list",
                )
