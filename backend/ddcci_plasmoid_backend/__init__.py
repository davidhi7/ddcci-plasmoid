import argparse
import pathlib


def get_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(prog="plasma-ddcci-backend")
    argument_parser.add_argument(
        "-d", "--debug", action="store_true", help="Print debug messages to stdout"
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
    sub_parsers.add_parser("version")
    sub_parsers.add_parser("detect")
    set_brightness_parser = sub_parsers.add_parser("set-brightness")
    set_brightness_parser.add_argument(
        "bus",
        type=int,
        help="Number of the i2c bus of the monitor. E.g. 1 for bus /dev/i2c-1",
    )
    set_brightness_parser.add_argument(
        "brightness",
        type=int,
        help="New brightness level for the monitor. Must be between 0 and 100.",
    )

    return argument_parser
