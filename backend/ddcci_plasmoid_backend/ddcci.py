import asyncio
import logging
import re
import subprocess
from typing import TypedDict

from ddcci_plasmoid_backend.ddcutil_parser import Node

logger = logging.getLogger(__name__)
brightness_feature_code = 0x10


class CommandOutput(TypedDict):
    returnCode: int
    stdout: str
    stderr: str


async def detect():
    async def fetch_monitor_data(node: Node):
        display_id = get_monitor_id(node)
        display_name = get_EDID_value(node, 'Model')
        bus_id = int(re.search(r'\d+$', node.child_by_key['I2C bus'].value).group())

        cmd = f'ddcutil getvcp --bus {bus_id} --brief {brightness_feature_code:x}'
        proc = await asyncio.subprocess.create_subprocess_shell( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode > 0:
            logger.debug(
                f'{display_name} id={display_id}: Return code {proc.returncode} when fetching the current brightness')
            raise subprocess.CalledProcessError(returncode=proc.returncode, cmd=cmd, output=stdout, stderr=stderr)

        _, _, _, display_brightness_raw, _ = stdout.decode().split(' ')

        return {
            'id': display_id,
            'name': display_name,
            'bus_id': bus_id,
            'brightness': int(display_brightness_raw)
        }

    output = subprocess_wrapper('ddcutil detect')
    content = Node.parse_indented_text(output['stdout'].split('\n'))

    found_serial_numbers = []
    awaitables = []
    for child in content.children:
        if not re.fullmatch(r'Display \d+', child.key.strip()):
            continue
        # monitors connected to DisplayPort may appear twice. This is apparently related to DisplayPort MST.
        # Since the EDID data of both entries is identical, we simply remove duplicate monitors based on their serial
        # number
        serial_number = get_EDID_value(child, 'Serial number')
        if serial_number in found_serial_numbers:
            logger.debug(
                f'{get_EDID_value(child, "Model")} id={get_monitor_id(child)}: Duplicate monitor found and removed'
            )
            continue
        found_serial_numbers.append(serial_number)
        awaitables.append(fetch_monitor_data(child))

    return await asyncio.gather(*awaitables, return_exceptions=True)


def set_brightness(bus_id: int, brightness: int) -> None:
    subprocess_wrapper(f'ddcutil setvcp --bus {bus_id} {brightness_feature_code:x} {brightness}')


def get_EDID_value(node: Node, value: str) -> str:
    return node.child_by_key['EDID synopsis'].child_by_key[value].value


def get_monitor_id(node: Node):
    return int(re.search(r'\d+', node.key).group())


def subprocess_wrapper(cmd: str) -> CommandOutput:
    logger.debug('Execute command: `' + cmd + '`')
    proc = subprocess.run(cmd.split(' '), capture_output=True, check=True)
    returnCode = proc.returncode

    return {
        'returnCode': returnCode,
        'stdout': proc.stdout.decode(),
        'stderr': proc.stderr.decode(),
    }
