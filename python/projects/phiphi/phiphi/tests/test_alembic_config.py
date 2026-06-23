"""Test Alembic config helpers."""

import configparser

from phiphi.migrations.alembic_config import escape_configparser_interpolation


def test_escape_configparser_interpolation_allows_percent_encoded_database_urls() -> None:
    """Store percent-encoded database passwords in Alembic's ConfigParser config."""
    database_url = "postgresql+psycopg://user:y-%29~8i%3Amu%3CX1@db.example.com:5432/app"
    escaped_url = escape_configparser_interpolation(database_url)

    parser = configparser.ConfigParser()
    parser.add_section("alembic")
    parser.set("alembic", "sqlalchemy.url", escaped_url)

    assert parser.get("alembic", "sqlalchemy.url") == database_url
