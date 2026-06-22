"""Superset constants."""

from pathlib import Path

# Path to the template dashboard export within the superset module
TEMPLATE_PATH = Path(__file__).parent / "templates" / "standard_v1"

# Dataset table names expected in the template
DATASET_TABLES = [
    "tabulated_messages",
    "post_class_connections",
    "post_class_tabulated_messages",
]
