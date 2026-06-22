"""Test project_db.py module."""

from unittest import mock

from phiphi import project_db

DEFAULT_BQ_PROJECT = "default_bq_project"


@mock.patch("google.auth.default", return_value=(None, DEFAULT_BQ_PROJECT))
def test_form_bigquery_sqlalchmey_uri(mock_auth):
    """Test form bigquery sqlalchemy uri."""
    assert (
        project_db.form_bigquery_sqlalchmey_uri("test") == f"bigquery://{DEFAULT_BQ_PROJECT}/test"
    )
