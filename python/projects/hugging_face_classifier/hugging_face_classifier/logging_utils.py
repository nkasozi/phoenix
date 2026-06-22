"""Logging utils for hugging face classifier.

This module provides utilities for configuring logging in the project.
It supports loading logging configurations from YAML or JSON files,
and allows for easy retrieval of loggers for specific modules.

Use the ENV variable `LOGGING_CONFIG_FILE` to specify a custom logging
configuration file path. If not set, it defaults to `default_logging.yaml`
"""

import json
import logging
import logging.config
import os
from pathlib import Path
from typing import Any

import yaml

ENV_CONFIG_VAR = "LOGGING_CONFIG_FILE"
DEFAULT_LOGGING_CONFIG = "default_logging.yaml"


def _load_yaml_config(path: str) -> Any:
    """Load a YAML logging configuration from the given file path."""
    with open(path, "rt", encoding="utf-8") as file_stream:
        return yaml.safe_load(file_stream)


def _load_json_config(path: str) -> Any:
    """Load a JSON logging configuration from the given file path."""
    with open(path, "rt", encoding="utf-8") as file_stream:
        return json.load(file_stream)


def configure_logging(config_path: str) -> None:
    """Configure the Python logging subsystem from a YAML or JSON config file.

    The file extension determines the parser (.yaml/.yml → YAML; .json → JSON).
    """
    # Check if the config file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Logging config file not found: {config_path}")
    _, ext = os.path.splitext(config_path.lower())
    if ext in (".yaml", ".yml"):
        config = _load_yaml_config(config_path)
    elif ext == ".json":
        config = _load_json_config(config_path)
    else:
        raise ValueError(f'Unsupported config file extension "{ext}". Use .yaml, .yml, or .json.')
    logging.config.dictConfig(config)


def _get_default_config_path() -> str:
    """Get the default logging config file path relative to this module."""
    module_dir = Path(__file__).parent.parent
    return str(module_dir / DEFAULT_LOGGING_CONFIG)


def get_module_logger(module_name: str) -> logging.Logger:
    """Get a logger for the specified module name.

    Including configuring the logging based on a YAML or JSON config file.
    """
    config_file = os.getenv(ENV_CONFIG_VAR, _get_default_config_path())
    configure_logging(config_file)
    return logging.getLogger(module_name)
