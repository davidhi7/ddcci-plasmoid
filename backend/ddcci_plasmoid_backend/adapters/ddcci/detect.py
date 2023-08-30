from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from ddcci_plasmoid_backend.adapters import ddcci_adapter
from ddcci_plasmoid_backend.adapters.ddcci.serial_numbers import SerialNumbers
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    ContinuousValue,
    NonContinuousValue,
    Property,
)
from ddcci_plasmoid_backend.subprocess_wrappers import CalledProcessError
from ddcci_plasmoid_backend.tree import Node

if TYPE_CHECKING:
    from ddcci_plasmoid_backend.adapters.ddcci.ddcutil_wrapper import DdcutilWrapper

logger = logging.getLogger(__name__)


async def ddcutil_detect_monitors(
        ddcutil_wrapper: DdcutilWrapper,
) -> list[ddcci_adapter.DdcciMonitor]:
    """
    Detect all connected monitors supporting DDC/CI including their capabilities and feature values.

    Returns:
        List of all detected monitors.
    """
    logger.info("Detect connected DDC/CI monitors")
    detect_output = await ddcutil_wrapper.run_async("detect", logger=logger)
    parsed_output = Node.parse_indented_text(detect_output.stdout.split("\n"))
    logger.debug(f"Found {len(parsed_output.children)} entries at root level")

    identified_monitors: list[SerialNumbers] = []
    monitor_tasks = []
    for monitor_node in parsed_output.children:
        # Try to get the ddcutil monitor id. If this fails, the node is likely not representing a functional DDC/CI
        # monitor.
        try:
            ddcutil_id = _get_ddcutil_monitor_id(monitor_node)
        except ValueError:
            logger.warning(
                f"Key `{monitor_node.key}` does not match pattern for a valid monitor, skip it"
            )
            continue

        if monitor_node.child_by_key["VCP version"].value == "Detection failed":
            logger.warning(f"{ddcutil_id=}: VCP version detection failed, skip it")
            continue

        monitor_identification = _get_monitor_identification(monitor_node)
        if monitor_identification in identified_monitors:
            logger.warning(f"{ddcutil_id=}: Duplicate monitor found, skip it")
            continue

        identified_monitors.append(monitor_identification)
        monitor_tasks.append(
            asyncio.create_task(
                _gather_monitor_data(ddcutil_wrapper, ddcutil_id, monitor_node)
            )
        )

    monitors = await asyncio.gather(*monitor_tasks, return_exceptions=True)
    count_all = len(monitors)
    # Filter exception objects that indicate that monitor detection failed
    for entry in list(monitors):
        if isinstance(entry, Exception):
            logger.warning("Failed to retrieve data for one monitor: %s", str(entry))
            monitors.remove(entry)
    count_filtered = len(monitors)
    count_remaining = count_all - count_filtered
    logger.info(
        f'Detected {count_filtered} working monitor {"bus" if count_filtered == 1 else "busses"}, '
        f'{count_remaining} malfunctioning {"bus" if count_remaining == 1 else "busses"}.'
    )
    return monitors


async def _gather_monitor_data(
        ddcutil_wrapper: DdcutilWrapper, ddcutil_id: int, monitor: Node
) -> ddcci_adapter.DdcciMonitor:
    """
    Gather monitor EDID data, parse monitor capabilities and fetch current feature values.

    Args:
        ddcutil_id: i2c bus id
        monitor: Node representing one monitor reported by `ddcutil detect`

    Returns:
        Dataclass representing a monitor

    Raises:
        subprocess_wrappers.CalledProcessError: Failed to parse VCP features.
    """
    local_logger = logging.getLogger(__name__ + f" ddcutil_id={ddcutil_id}")
    # Retrieve bus_id and EDID data
    bus_id = int(re.search(r"\d+$", monitor.child_by_key["I2C bus"].value).group())

    try:
        monitor_name = monitor.walk("EDID synopsis", "Model")
    except ValueError:
        local_logger.warning("Monitor model name unavailable")
        monitor_name = "Unknown monitor"

    # Retrieve capabilities and vcp feature values
    try:
        capabilities = await _parse_capabilities(ddcutil_wrapper, bus_id)
    except CalledProcessError:
        local_logger.warning("Failed to parse monitor capabilities, skip it")
        raise

    vcp_values: dict[Property, ContinuousValue | NonContinuousValue] = {}
    # Concurrent ddcutil calls on the same i2c bus would fail
    if ddcci_adapter.FeatureCode.BRIGHTNESS.value in capabilities:
        vcp_values[Property.BRIGHTNESS] = ContinuousValue(
            value=await _get_vcp_value(
                ddcutil_wrapper, bus_id, ddcci_adapter.FeatureCode.BRIGHTNESS.value
            ),
            min_value=0,
            max_value=100,
        )
    if ddcci_adapter.FeatureCode.CONTRAST.value in capabilities:
        vcp_values[Property.CONTRAST] = ContinuousValue(
            value=await _get_vcp_value(
                ddcutil_wrapper, bus_id, ddcci_adapter.FeatureCode.CONTRAST.value
            ),
            min_value=0,
            max_value=100,
        )
    if ddcci_adapter.FeatureCode.POWER_MODE.value in capabilities:
        vcp_values[Property.POWER_MODE] = NonContinuousValue(
            value=await _get_vcp_value(
                ddcutil_wrapper, bus_id, ddcci_adapter.FeatureCode.POWER_MODE.value
            ),
            choices=capabilities[ddcci_adapter.FeatureCode.POWER_MODE.value],
        )

    return ddcci_adapter.DdcciMonitor(
        ddcutil_id=ddcutil_id,
        name=monitor_name,
        bus_id=bus_id,
        vcp_capabilities=capabilities,
        property_values=vcp_values,
    )


def _get_monitor_identification(monitor: Node) -> SerialNumbers:
    """
    Create a `SerialNumbers` object for identifying unique monitors.

    Args:
        monitor: Node representing one monitor reported by `ddcutil detect`

    Returns:
        `SerialNumbers` object containing the serial number and the binary serial number if available.
    """
    local_logger = logging.getLogger(
        __name__ + f" ddcutil_id={_get_ddcutil_monitor_id(monitor)}"
    )
    serial_number = None
    binary_serial_number = None
    try:
        serial_number = monitor.walk("EDID synopsis", "Serial number").strip()
    except ValueError:
        local_logger.warning("Serial number unavailable")

    try:
        binary_serial_number = monitor.walk(
            "EDID synopsis", "Binary serial number"
        ).strip()
    except ValueError:
        local_logger.warning("Binary serial number unavailable")
    return SerialNumbers(serial_number, binary_serial_number)


def _get_ddcutil_monitor_id(monitor: Node) -> int:
    """
    Return the monitor id of an already parsed Node object representing a monitor.

    Args:
        monitor: Node representing one monitor reported by `ddcutil detect`

    Returns:
        Integer value

    Raises:
        ValueError: The node does not represent a valid monitor: Its top level key is not `Display %i` where %i is the
        display id
    """
    key = monitor.key.strip()
    if not re.fullmatch(r"Display \d+", key):
        msg = f"`{key}` is not a valid ddcutil detect header"
        raise ValueError(msg)
    return int(re.search(r"\d+", key).group())


async def _get_vcp_value(
        ddcutil_wrapper: DdcutilWrapper, bus: int, feature_code: int
) -> int:
    """
    Query the value of a continuous or non-continuous vcp feature.

    Args:
        ddcutil_wrapper: i2c bus id
        feature_code: Vcp feature code

    Returns:
        Integer value

    Raises:
        subprocess_wrappers.CalledProcessError: The underlying ddcutil command fails.
    """
    result = await ddcutil_wrapper.run_async(
        "getvcp", "--brief", hex(feature_code), bus=bus, logger=logger
    )
    feature_value = result.stdout.split(" ")[3]
    # if the value is returned in hexadecimal format, it begins with 'x'.
    # `int` fails in this case, so we add a leading 0.
    return (
        int(feature_value)
        if feature_value.isnumeric()
        else int("0" + feature_value, 16)
    )


async def _parse_capabilities(
        ddcutil_wrapper: DdcutilWrapper, bus: int
) -> ddcci_adapter.VcpFeatureList:
    """
    Parse the capabilities string of a monitor.

    Args:
        bus: i2c bus id

    Returns:
        Dict of supported feature codes and accepted values for non-continuous features or None for continuous features.

    Raises:
        subprocess_wrappers.CalledProcessError: The underlying ddcutil command fails.
    """
    parsed_features: ddcci_adapter.VcpFeatureList = {}
    output = await ddcutil_wrapper.run_async(
        "capabilities", "--brief", bus=bus, logger=logger
    )
    # This is what a sample capabilities string looks like:
    #  Unparsed capabilities string: (prot(monitor)type(LCD)model(S2721DGFA)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 10
    #  12 14(05 08 0B 0C) 16 18 1A 52 60(0F 11 12 ))mswhql(1)asset_eep(40)mccs_ver(2.1))
    capabilities_string = output.stdout
    # Extract the `vcp(...) part from the capabilities string
    vcp_features_enumeration = re.search(
        r"vcp\(([\dA-F\s]|(\([\dA-F\s]+\)))+\)", capabilities_string
    )
    # Prevent fail if the `vcp()` section is empty (primarily for debugging)
    if not vcp_features_enumeration:
        return {}
    # Extract the feature code and their values if not continuous
    vcp_features = re.findall(
        r"([\dA-F]+)(\([\dA-F\s]+\))?", vcp_features_enumeration.group()
    )
    for code, values in vcp_features:
        is_continuous_feature = values == ""
        if is_continuous_feature:
            parsed_features[int(code, 16)] = None
        else:
            parsed_features[int(code, 16)] = [
                int(value, 16) for value in re.findall(r"[\dA-F]+", values)
            ]

    return parsed_features
