"""Test AutheRemoteUserViewCustom."""

import unittest

import pytest
from flask import Flask
from flask_appbuilder import SQLA, AppBuilder  # type: ignore[import-untyped]
from flask_appbuilder.const import AUTH_REMOTE_USER  # type: ignore[import-untyped]

from phoenix_superset import custom_sso_manager


class AuthRemoteUserTestCase(unittest.TestCase):
    """Test AuthRemoteUser."""

    def setUp(self):
        """Setup."""
        # start Flask
        self.app = Flask(__name__)
        self.app.config["AUTH_TYPE"] = AUTH_REMOTE_USER
        # Debug mode so that exceptions are raised instead of returning 500 responses
        # to allow for easier debugging of tests
        self.app.config["DEBUG"] = True
        self.app.config["SECRET_KEY"] = "thisismys"

        # start Database
        self.db = SQLA(self.app)

        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down."""
        # Remove test user
        user_alice = self.appbuilder.sm.find_user("alice")
        if user_alice:
            self.db.session.delete(user_alice)
            self.db.session.commit()

        # stop Flask
        delattr(self, "app")

        # stop Flask-AppBuilder
        delattr(self, "appbuilder")

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

    def test_login_error_with_debug(self):
        """Test login error is correct."""
        self.appbuilder = self.create_appbuilder()
        # Simulate logging in
        with self.client as c:
            with pytest.raises(Exception) as e:
                c.get("/login/")
                self.assertIn(
                    "The REMOTE_USER header is not set and no login URL",
                    str(e.value),
                )

    def test_login_error(self):
        """Test login error is correct."""
        self.app.config["DEBUG"] = False
        self.appbuilder = self.create_appbuilder()
        # Simulate logging in
        with self.client as c:
            response = c.get("/login/")
            self.assertEqual(response.status_code, 500)

    def test_login_authenticated_user(self):
        """Test login authenticated user."""
        self.appbuilder = self.create_appbuilder()
        self.client = self.app.test_client()
        sm = self.appbuilder.sm
        # register a user
        alice_user = sm.add_user(
            username="alice",
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            role=[],
        )
        response = self.client.get("/login/", environ_base={"REMOTE_USER": alice_user.email})
        assert response.status_code == 302  # Expecting a redirect
        # This should go back to home page
        assert response.headers["Location"] == "/"

    def test_login_user_not_found(self):
        """Test login user not found."""
        login_redirect_url = "/some_other_url"
        self.app.config["LOGIN_REDIRECT_URL"] = login_redirect_url
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
        response = self.client.get("/login/", environ_base={"REMOTE_USER": "NOT_FOUND"})
        assert response.status_code == 401

    def test_login_no_auth_header(self):
        """Test login with no auth header."""
        login_redirect_url = "/some_other_url"
        self.app.config["LOGIN_REDIRECT_URL"] = login_redirect_url
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
        response = self.client.get("/login/")
        assert response.status_code == 302
        assert response.headers["Location"] == login_redirect_url

    def test_login_session(self):
        """Test login authenticated user.

        Ie. if the user has a session already.
        """
        self.appbuilder = self.create_appbuilder()
        self.client = self.app.test_client()
        sm = self.appbuilder.sm
        # register a user
        alice_user = sm.add_user(
            username="alice",
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            role=[],
        )
        with self.client as c:
            c.get("/login/", environ_base={"REMOTE_USER": alice_user.email})
            with c.session_transaction() as sess:
                sess["_user_id"] = alice_user.id
            response = c.get("/login/", environ_base={"REMOTE_USER": alice_user.email})
            assert response.status_code == 302
            assert response.headers["Location"] == "/"
            # Check that the before_request works
            response = c.get("/auth_check/", environ_base={"REMOTE_USER": alice_user.email})
            assert response.status_code == 200
            with c.session_transaction() as sess:
                assert "_user_id" in sess
                assert sess["_user_id"] == alice_user.id

    def test_login_session_header_change(self):
        """Test login session with the header changed.

        If the user is logged in and then logs in to a different user.
        """
        login_redirect_url = "/some_other_url"
        self.app.config["LOGIN_REDIRECT_URL"] = login_redirect_url
        self.appbuilder = self.create_appbuilder()
        self.client = self.app.test_client()
        sm = self.appbuilder.sm
        # register a user
        alice_user = sm.add_user(
            username="alice",
            first_name="Alice",
            last_name="Doe",
            email="alice@example.com",
            role=[],
        )
        with self.client as c:
            c.get("/login/", environ_base={"REMOTE_USER": alice_user.email})
            with c.session_transaction() as sess:
                sess["_user_id"] = alice_user.id
            # This will run the before_request and thus should log out the user
            response = c.get("/auth_check/", environ_base={"REMOTE_USER": "NOT_FOUND"})
            assert response.status_code == 302
            assert response.headers["Location"] == "/login/"
            # User should be logged out now
            with c.session_transaction() as sess:
                assert "_user_id" not in sess

            # Check that the login works again and there are no loop
            c.get("/login/", environ_base={"REMOTE_USER": alice_user.email})
            with c.session_transaction() as sess:
                sess["_user_id"] = alice_user.id
            response = c.get("/login/", environ_base={"REMOTE_USER": "NOT_FOUND"})
            assert response.status_code == 302
            assert response.headers["Location"] == "/login/"
            with c.session_transaction() as sess:
                assert "_user_id" not in sess
            # Check that there is no loop
            response = c.get("/login/", environ_base={"REMOTE_USER": "NOT_FOUND"})
            assert response.status_code == 401
