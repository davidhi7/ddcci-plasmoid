from __future__ import annotations

import logging
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Final

from ddcci_plasmoid_backend.errors import ConfigurationError

logger = logging.getLogger(__name__)

CONFIG_DIR: Final[Path] = (
    Path(os.path.expandvars("$XDG_CONFIG_HOME"))
    if "XDG_CONFIG_HOME" in os.environ
    else Path("~/.config").expanduser()
)
DEFAULT_CONFIG_PATH: Final[Path] = CONFIG_DIR / "ddcci_plasmoid/config.ini"

# Template that provides types and default values to all expected configuration values
CONFIG_SCHEME = {
    "ddcci": {
        "ddcutil_executable": {"type": str, "default": "ddcutil"},
        "ddcutil_sleep_multiplier": {"type": int, "default": 1},
        "ddcutil_no_verify": {"type": bool, "default": False},
        "brute_force_attempts": {"type": int, "default": 0},
    }
}


def init(config_path: Path | None = None) -> ConfigParser:
    """Create a new configuration instance. If config_path is not None, read the given configuration
    file. If configuration keys and sections are missing, they are created to match CONFIG_SCHEME.

    Args:
        config_path: Path to the configuration file. If None, create a new configuration file from
        scratch. If the file does not exist, it is not created.

    Returns:

    """
    config = ConfigParser()
    if config_path and config_path.is_file():
        with config_path.open() as file:
            logger.info(f"Read config file `{config_path}`")
            config.read_file(file)
    else:
        logger.info(f"Config file `{config_path}` unavailable")

    # Insert default options if missing
    for section, pairs in CONFIG_SCHEME.items():
        if section not in config.sections():
            config.add_section(section)
        for key, value in pairs.items():
            if key not in config[section].keys():
                config[section][key] = str(value["default"])
    return config


def set_config_value(
    config_instance: ConfigParser,
    section: str,
    key: str,
    value: str,
    *,
    save_file_path: Path | None = None,
) -> None:
    """Write a value to the given configuration instance, then optionally save it.
    The value is validated using CONFIG_SCHEME.

    Args:
        config_instance: ConfigParser instance to work on
        section: Configuration section
        key: Configuration key within the section
        value: Configuration value
        save_file_path: Path to save file to. If None, the configuration is not saved to a file.

    Returns:
        None
    """
    if section not in CONFIG_SCHEME.keys():
        msg = f"Section `{section}` does not exist"
        raise ConfigurationError(msg)
    if key not in CONFIG_SCHEME[section].keys():
        msg = f"Key `{section}` does not exist within section `{section}`"
        raise ConfigurationError(msg)
    # Try to parse the value and then convert it back into a string, to test whether the value is
    # acceptable and to normalize it
    normalized_value: str
    try:
        normalized_value = str(CONFIG_SCHEME[section][key]["type"](value))
    except ValueError as err:
        msg = f"Value `{value}` is invalid for the key `{section}.{key}`"
        raise ConfigurationError(msg) from err
    # Here we do not create a new section to the ConfigParser if it is missing because all sections
    # in a template-compliant ConfigParser are already there
    config_instance[section][key] = normalized_value
    if save_file_path:
        with save_file_path.open("w") as file:
            config_instance.write(file)
            logger.info(f"Saved config file `{save_file_path}`")


# Main config instance
config: Final[ConfigParser] = init(DEFAULT_CONFIG_PATH)
