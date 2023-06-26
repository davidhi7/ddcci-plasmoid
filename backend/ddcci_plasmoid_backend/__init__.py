import argparse
import pathlib

from ddcci_plasmoid_backend.adapters.Monitor import Property
from ddcci_plasmoid_backend.adapters.adapters import monitor_adapters


def get_parser() -> argparse.ArgumentParser:
    interfaces = [adapter.label for adapter in monitor_adapters]
    properties = [property.value for property in Property]

    argument_parser = argparse.ArgumentParser(prog='plasma-ddcci-backend')
    argument_parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Write debug messages to stdout'
    )
    argument_parser.add_argument(
        '--debug-log',
        action='store',
        type=pathlib.Path,
        metavar='LOG_FILE',
        help='Write debug messages to LOG_FILE'
    )
    sub_parsers = argument_parser.add_subparsers(
        title='commands',
        dest='command',
        required=True
    )
    sub_parsers.add_parser('version', help='Print the backend version')

    detect_parser = sub_parsers.add_parser('detect', help='Detect connected monitors')
    detect_parser.add_argument(
        'adapter',
        choices=interfaces,
        help='Target monitor adapters',
        nargs='+'
    )

    set_parser = sub_parsers.add_parser('set', help='Write a value to a monitor')
    set_parser.add_argument(
        'adapter',
        choices=interfaces,
        help='Target monitor adapter'
    )
    set_parser.add_argument(
        'id',
        type=int,
        help='Monitor identification (`detect` key)'
    )
    set_parser.add_argument(
        'property',
        choices=properties,
        help='Monitor property'
    )
    set_parser.add_argument(
        'value',
        type=int,
        help='New value'
    )

    return argument_parser
