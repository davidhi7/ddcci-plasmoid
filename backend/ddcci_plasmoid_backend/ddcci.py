import asyncio
import logging
import re
import subprocess
from typing import TypedDict, Optional

from ddcci_plasmoid_backend.Node import Node

logger = logging.getLogger(__name__)
brightness_feature_code = 0x10


class CommandOutput(TypedDict):
    returnCode: int
    stdout: str
    stderr: str


class MonitorData(TypedDict):
    id: int
    name: str
    bus_id: int
    brightness: int


# Record for identifying a monitor by its `Serial number` as well as `Binary serial number` EDID value reported by
# ddcutil to look for duplicate monitors. Issue #1 shows that comparing by Serial number only is not sufficient, as the
# monitors of the reporter only reported a binary serial number.
class MonitorID:
    def __init__(self, serial_number: str, binary_serial_number: str):
        self.serial_number = serial_number
        self.binary_serial_number = binary_serial_number

    def __eq__(self, other: "MonitorID") -> bool:
        # If at least one serial number value is not empty, and they are not equal, they are different monitors
        if (
            self.serial_number or other.serial_number
        ) and self.serial_number != other.serial_number:
            return False
        if (
            self.binary_serial_number or other.binary_serial_number
        ) and self.binary_serial_number != other.binary_serial_number:
            return False
        return True


async def detect():
    async def fetch_monitor_data(node: Node) -> MonitorData:
        display_id = get_monitor_id(node)
        display_name = ""
        if "EDID synopsis" in node.child_by_key:
            display_name = get_EDID_value(node, "Model")
        # Use generic name if the EDID model is either empty or not present
        if not display_name:
            display_name = "Unknown display"

        bus_id = int(re.search(r"\d+$", node.child_by_key["I2C bus"].value).group())

        result = await async_subprocess_wrapper(
            f"ddcutil getvcp --bus {bus_id} --brief {brightness_feature_code:x}"
        )

        _, _, _, display_brightness_raw, _ = result["stdout"].split(" ")

        return {
            "id": display_id,
            "name": display_name,
            "bus_id": bus_id,
            "brightness": int(display_brightness_raw),
        }

    output = subprocess_wrapper("ddcutil detect")
    content = Node.parse_indented_text(output["stdout"].split("\n"))
    logger.debug(f"Found {len(content.children)} entries at root level")

    found_monitors: list[MonitorID] = []
    awaitables = []
    for child in content.children:
        if not re.fullmatch(r"Display \d+", child.key.strip()):
            logger.debug(
                f"Key {child.key.strip()} does not match pattern for valid display, so skip it"
            )
            continue
        monitor_id = get_monitor_id(child)
        if child.child_by_key["VCP version"].value == "Detection failed":
            logger.debug(
                f"Display ddcutil_id={monitor_id} VCP version detection failed, so skip it"
            )
            continue
        if "EDID synopsis" in child.child_by_key:
            # monitors connected to DisplayPort may appear twice. This is apparently related to DisplayPort MST.
            # Since the EDID data of both entries is identical, we simply remove duplicate monitors based on their
            # serial number
            monitorId = MonitorID(
                serial_number=get_EDID_value(child, "Serial number"),
                binary_serial_number=get_EDID_value(child, "Binary serial number"),
            )
            if monitorId in found_monitors:
                logger.debug(
                    f'{get_EDID_value(child, "Model")} id={monitor_id}: Duplicate monitor found and removed'
                )
                continue
            found_monitors.append(monitorId)
        else:
            # For the unlikely case that no EDID synopsis is included, skip all duplication tests
            logger.debug(f"id={monitor_id} No EDID synopsis returned")

        awaitables.append(fetch_monitor_data(child))

    return await asyncio.gather(*awaitables, return_exceptions=True)


def set_brightness(bus_id: int, brightness: int) -> None:
    subprocess_wrapper(
        f"ddcutil setvcp --bus {bus_id} {brightness_feature_code:x} {brightness}"
    )


def get_EDID_value(node: Node, value: str) -> Optional[str]:
    node = node.child_by_key["EDID synopsis"].child_by_key.get(value)
    if node:
        return node.value
    return None


def get_monitor_id(node: Node):
    return int(re.search(r"\d+", node.key).group())


# Wrap sync and async subprocess calls for mocking
def subprocess_wrapper(cmd: str) -> CommandOutput:
    logger.debug("Execute command: `" + cmd + "`")
    proc = subprocess.run(cmd.split(" "), capture_output=True)
    stdout = strip_ddcutil_stdout_warnings(proc.stdout.decode())
    stderr = proc.stderr.decode()
    command_output = {
        "returnCode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
    }

    log_subprocess_output(cmd, command_output)
    if proc.returncode > 0:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode, cmd=cmd, output=stdout, stderr=stderr
        )
    return command_output


async def async_subprocess_wrapper(cmd: str) -> CommandOutput:
    logger.debug("Execute command: `" + cmd + "`")
    proc = await asyncio.subprocess.create_subprocess_shell(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # it's safe to assume that the return code is not None at this point
    return_code: int = 1 if proc.returncode is None else proc.returncode
    stdout, stderr = await proc.communicate()
    stdout = strip_ddcutil_stdout_warnings(stdout.decode())
    stderr = stderr.decode()
    command_output = {
        "returnCode": return_code,
        "stdout": stdout,
        "stderr": stderr,
    }

    log_subprocess_output(cmd, command_output)
    if proc.returncode > 0:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode, cmd=cmd, output=stdout, stderr=stderr
        )
    return command_output


def strip_ddcutil_stdout_warnings(stdout: str) -> str:
    # Fix #32
    stdout = stdout.replace(
        "(is_nvidia_einval_bug          ) nvida/i2c-dev bug encountered. Forcing future io I2C_IO_STRATEGY_FILEIO. "
        "Retrying\n",
        "",
    )
    # Fix 49
    return re.sub(
        (
            r"busno=\d+, Feature 0x.+ should not exist but ddc_get_nontable_vcp_value\(\) succeeds"
            r", returning mh=0x.+ ml=0x.+ sh=0x.+ sl=0x.+\n"
        ),
        "",
        stdout,
    )


def log_subprocess_output(cmd: str, output: CommandOutput):
    # remove trailing newlines for better readability
    stripped_stdout = re.sub(r"\n$", "", output["stdout"])
    stripped_stderr = re.sub(r"\n$", "", output["stderr"])
    logger.debug(f'[code]   {cmd}: {output["returnCode"]}')
    logger.debug(f"[stdout] {cmd}: {stripped_stdout}")
    logger.debug(f"[stderr] {cmd}: {stripped_stderr}\n")
