from __future__ import annotations

import asyncio
import getpass
import json
import logging
import re
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import NoReturn

import fasteners

from ddcci_plasmoid_backend import ddcci
from ddcci_plasmoid_backend.__init__ import get_parser


def get_ddcutil_version() -> str:
    result = subprocess.run(
        ["ddcutil", "--version"], check=True, stdout=subprocess.PIPE
    )
    # First line of ddcutil output contains the version
    version_line = result.stdout.decode().split("\n")[0]
    # Remove all characters from this line except for points followed by a number
    # This is supposed to extract the version (x.y.z) from the string
    return re.sub(r"(?!\.\d)\D", "", version_line)


def main():
    arguments = vars(get_parser().parse_args())

    logging_formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")

    logging.getLogger().setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging_formatter)
    stream_handler.setLevel(logging.DEBUG if arguments["debug"] else logging.INFO)
    logging.getLogger().addHandler(stream_handler)

    if arguments["debug_log"]:
        log_path: Path = arguments["debug_log"]
        # Fail if log_path exists but is not a file
        if not log_path.is_file() and log_path.exists():
            logging.debug("`LOG_FILE` must be a valid file")
        else:
            logging.debug(f"Writing logs to file {log_path}")
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging_formatter)
            file_handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(file_handler)

    # supress log message `DEBUG asyncio: Using selector: EpollSelector`
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.debug(f'backend version: {version("ddcci-plasmoid-backend")}')
    logger.debug(f"ddcutil version: {get_ddcutil_version()}")

    def handle_error(error: str | subprocess.CalledProcessError) -> NoReturn:
        if isinstance(error, subprocess.CalledProcessError):
            error = error.stderr if error.stderr else error.stdout
        print(
            json.dumps(
                {"command": arguments["command"], "error": error.replace("\n", " ")}
            )
        )
        sys.exit(1)

    logger.debug(f'argv: {" ".join(sys.argv)}')

    if arguments["command"] == "version":
        print(version("ddcci-plasmoid-backend"))
        sys.exit(0)

    # include the username in the lock file. Otherwise, if user A creates a lock, user B may not have the permissions
    # to access the lock file and this program will fail until the lock file is deleted.
    # Using `os.getlogin()` may fail on some configurations (#19)
    with fasteners.InterProcessLock(
        Path(tempfile.gettempdir()) / f"ddcci_plasmoid_backend-{getpass.getuser()}.lock"
    ):
        if arguments["command"] == "detect":
            try:
                result = asyncio.run(ddcci.detect())
            except subprocess.CalledProcessError as err:
                logger.debug(err)
                handle_error(err)
            except Exception as err:
                logger.debug(err)
                handle_error("Failed to fetch monitor data")

            count = len(result)
            # Remove objects that are errors
            for report in result:
                if isinstance(report, Exception):
                    logger.debug(report)
                    result.remove(report)
            # filtered_results = [report for report in result if isinstance(report, dict)]

            filtered_count = len(result)
            remaining_count = count - filtered_count

            logger.debug(
                f'Detected {filtered_count} working monitor {"bus" if filtered_count == 1 else "busses"}, '
                f'{remaining_count} non-working {"bus" if remaining_count == 1 else "busses"}.'
            )

            print(json.dumps({"command": "detect", "value": result}))
        elif arguments["command"] == "set-brightness":
            bus_id = arguments["bus"]
            brightness = arguments["brightness"]
            if brightness < 0 or brightness > 100:
                handle_error(
                    f"Illegal value {brightness} for `brightness`, must be between 0 and 100"
                )

            try:
                ddcci.set_brightness(bus_id, brightness)
                print(
                    json.dumps(
                        {
                            "command": "set-brightness",
                            "value": {"bus_id": bus_id, "brightness": brightness},
                        }
                    )
                )
            except subprocess.CalledProcessError as err:
                logger.debug(err)
                handle_error(err)

    sys.exit(0)


if __name__ == "__main__":
    main()
