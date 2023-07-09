from __future__ import annotations

import asyncio
import getpass
import json
import logging
import re
import subprocess
import sys
import tempfile
import traceback
from importlib.metadata import version
from pathlib import Path
from typing import NoReturn

import fasteners

from ddcci_plasmoid_backend import get_parser, Property
from ddcci_plasmoid_backend.adapters import adapters


def get_ddcutil_version() -> str:
    # TODO log if ddcutil is not found in path
    result = subprocess.run(['ddcutil', '--version'], check=True, stdout=subprocess.PIPE)
    # First line of ddcutil output contains the version
    version_line = result.stdout.decode().split('\n')[0]
    # Remove all characters from this line except for points followed by a number
    # This is supposed to extract the version (x.y.z) from the string
    return re.sub(r'(?!\.\d)\D', '', version_line)


def handle_error(command: str, error: str | Exception) -> NoReturn:
    if isinstance(error, Exception):
        error = str(error)
    print(json.dumps({
        'command': command,
        'error': error.replace('\n', ' ')
    }))
    sys.exit(1)


def main():
    arguments = vars(get_parser().parse_args())

    logging_formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')

    logging.getLogger().setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging_formatter)
    stream_handler.setLevel(logging.DEBUG if arguments['debug'] else logging.INFO)
    logging.getLogger().addHandler(stream_handler)

    if arguments['debug_log']:
        log_path: Path = arguments['debug_log']
        # Fail if log_path exists but is not a file
        if not log_path.is_file() and log_path.exists():
            logging.debug('`LOG_FILE` must be a valid file')
        else:
            logging.debug(f'Writing logs to file {log_path}')
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging_formatter)
            file_handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(file_handler)

    # supress log message `DEBUG asyncio: Using selector: EpollSelector`
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.debug(f'backend version: {version("ddcci-plasmoid-backend")}')
    logger.debug(f'ddcutil version: {get_ddcutil_version()}')
    logger.debug(f'argv: {" ".join(sys.argv)}')

    if arguments['command'] == 'version':
        print(version('ddcci-plasmoid-backend'))
        sys.exit(0)

    # include the username in the lock file. Otherwise, if user A creates a lock, user B may not have the permissions
    # to access the lock file and this program will fail until the lock file is deleted.
    # Using `os.getlogin()` may fail on some configurations (#19)
    with fasteners.InterProcessLock(Path(tempfile.gettempdir()) / f'ddcci_plasmoid_backend-{getpass.getuser()}.lock'):
        try:
            if arguments['command'] == 'detect':
                adapter_args = [adapters.adapter_by_label(adapter) for adapter in arguments['adapter']]
                print(json.dumps({
                    'command': 'detect',
                    'response': asyncio.run(adapters.detect(adapter_args))
                }))
            elif arguments['command'] == 'set':
                adapter_arg = adapters.adapter_by_label(arguments['adapter'])
                property_arg = Property(arguments['property'])
                print(json.dumps({
                    'command': 'detect',
                    'response': asyncio.run(adapters.set_property(adapter_arg, property_arg, arguments['id'], arguments['value']))
                }))
                ...
                # bus_id = arguments['bus']
                # brightness = arguments['brightness']
                # if brightness < 0 or brightness > 100:
                #     handle_error(f'Illegal value {brightness} for `brightness`, must be between 0 and 100')
                #
                # try:
                #     ddcci.set_brightness(bus_id, brightness)
                #     print(json.dumps({
                #         'command': 'set-brightness',
                #         'value': {
                #             'bus_id': bus_id,
                #             'brightness': brightness
                #         }
                #     }))
                # except subprocess.CalledProcessError as err:
                #     logger.debug(err)
                #     handle_error(err)

        except Exception as exc:
            logger.debug(traceback.print_exc())
            handle_error('detect', exc)
    sys.exit(0)


if __name__ == '__main__':
    main()
