from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import logging
import pathlib
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from traceback import format_exception
from typing import TYPE_CHECKING, Callable, NoReturn

import fasteners

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters import adapters
from ddcci_plasmoid_backend.adapters.adapters import monitor_adapter_classes
from ddcci_plasmoid_backend.adapters.monitor_adapter import Property

if TYPE_CHECKING:
    from types import TracebackType


def configure_argument_parser() -> argparse.ArgumentParser:
    interfaces = monitor_adapter_classes.keys()
    properties = [property.value for property in Property]

    argument_parser = argparse.ArgumentParser(prog="ddcci-plasmoid-backend")
    argument_parser.add_argument(
        "-d", "--debug", action="store_true", help="Write debug messages to stdout"
    )
    argument_parser.add_argument(
        "--debug-log",
        action="store",
        type=pathlib.Path,
        metavar="LOG_FILE",
        help="Write debug messages to LOG_FILE",
    )
    sub_parsers = argument_parser.add_subparsers(
        title="commands", dest="command", required=True
    )
    sub_parsers.add_parser("version", help="Print the backend version")

    detect_parser = sub_parsers.add_parser("detect", help="Detect connected monitors")
    detect_parser.add_argument(
        "adapter", choices=interfaces, help="Target monitor adapters", nargs="+"
    )

    set_parser = sub_parsers.add_parser("set", help="Write a value to a monitor")
    set_parser.add_argument(
        "adapter", choices=interfaces, help="Target monitor adapter"
    )
    set_parser.add_argument(
        "id", type=int, help="Monitor identification (`detect` key)"
    )
    set_parser.add_argument("property", choices=properties, help="Monitor property")
    set_parser.add_argument("value", type=int, help="New value")

    set_all_parser = sub_parsers.add_parser(
        "set-all",
        help="Write a value to all monitors detected in the last `detect` call",
    )

    set_all_parser.add_argument("property", choices=properties, help="Monitor property")
    set_all_parser.add_argument("value", type=int, help="New value")

    # Simple conversion function to split configuration identifiers formatted as `section.key` into
    # separate variables, raising a ValueError if the argument is wrongly formatted
    def composed_config_key(argument: str) -> tuple[str, str]:
        section, key = argument.split(".")
        return section, key

    config_parser = sub_parsers.add_parser(
        "config", help="Get or set a configuration value"
    )
    config_parser.add_argument(
        "key", type=composed_config_key, help="Configuration key"
    )
    config_parser.add_argument("value", help="New configuration value", nargs="?")

    return argument_parser


def configure_root_logger(*, debug_mode: bool, debug_log: Path | None) -> None:
    logging_formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
    logging_level = logging.NOTSET if debug_mode else logging.CRITICAL + 1

    logging.getLogger().setLevel(logging_level)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging_formatter)
    stream_handler.setLevel(logging_level)
    logging.getLogger().addHandler(stream_handler)

    if debug_log:
        # Fail if log_path exists but is not a file
        if not debug_log.is_file() and debug_log.exists():
            logging.warning("`LOG_FILE` must be a valid file")
        else:
            logging.info("Writing logs to file `%s`", debug_log)
            file_handler = logging.FileHandler(debug_log)
            file_handler.setFormatter(logging_formatter)
            file_handler.setLevel(logging_level)
            logging.getLogger().addHandler(file_handler)

    # Supress log message `DEBUG asyncio: Using selector: EpollSelector`
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def print_output_json(command: str, **kwargs: str | dict | list) -> None:
    """Print kwargs to stdout formatted as json.

    Args:
        command: `command` property of the output
        **kwargs: Content of the output

    Returns:
        None
    """
    # By doing this, `command` is always the first key
    data = {"command": command}
    data.update(kwargs)
    print(json.dumps(data))


def get_custom_except_hook(command: str, logger: logging.Logger) -> Callable:
    def except_hook(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType | None,
    ) -> NoReturn:
        logger.exception(
            "Uncaught exception occurred", exc_info=(exc_type, exc_value, exc_traceback)
        )
        print_output_json(
            command,
            error={
                "type": exc_type.__name__,
                "value": str(exc_value),
                "traceback": format_exception(exc_type, exc_value, exc_traceback),
            },
        )
        sys.exit(1)

    return except_hook


def main() -> NoReturn:
    arguments = vars(configure_argument_parser().parse_args())
    configure_root_logger(
        debug_mode=arguments["debug"], debug_log=arguments["debug_log"]
    )
    logger = logging.getLogger(__name__)
    logger.info("backend version: %s", version("ddcci-plasmoid-backend"))
    logger.info("argv: %s", " ".join(sys.argv))
    sys.excepthook = get_custom_except_hook(arguments["command"], logger)
    config.config = config.init(config.DEFAULT_CONFIG_PATH)

    if arguments["command"] == "version":
        print(version("ddcci-plasmoid-backend"))
        sys.exit(0)
    elif arguments["command"] == "config":
        section, key = arguments["key"]
        # If a value argument is provided, the config value is set, otherwise it is only read
        if arguments["value"]:
            value = arguments["value"]
            config.set_config_value(
                config.config,
                section,
                key,
                value,
                save_file_path=config.DEFAULT_CONFIG_PATH,
            )
        print_output_json("config", response=config.config[section].get(key))
        sys.exit(0)

    # Include the username in the lock file. Otherwise, if user A creates a lock, user B may not
    # have the permissions to access the lock file and this program will fail until the lock file
    # is deleted. Using `os.getlogin()` may fail on some configurations (#19)
    with fasteners.InterProcessLock(
            Path(tempfile.gettempdir()) / f"ddcci_plasmoid_backend-{getpass.getuser()}.lock"
    ):
        if arguments["command"] == "detect":
            print_output_json(
                "command", response=asyncio.run(adapters.detect(arguments["adapter"]))
            )
        elif arguments["command"] == "set":
            asyncio.run(
                adapters.set_property(
                    arguments["adapter"],
                    arguments["property"],
                    arguments["id"],
                    arguments["value"],
                ))
            print_output_json("set")
        elif arguments["command"] == "set-all":
            asyncio.run(
                adapters.set_all_monitors(arguments["property"], arguments["value"])
            )
            print_output_json("set-all")

    sys.exit(0)


if __name__ == "__main__":
    main()
