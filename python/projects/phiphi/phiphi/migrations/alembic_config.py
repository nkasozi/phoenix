"""Helpers for values passed through Alembic's ConfigParser-backed config."""


def escape_configparser_interpolation(value: str) -> str:
    """Escape percent signs so ConfigParser stores generated URLs literally."""
    return value.replace("%", "%%")
