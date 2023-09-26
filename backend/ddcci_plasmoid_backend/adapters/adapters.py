from __future__ import annotations

import asyncio
import json
import logging
from functools import reduce
from typing import Dict

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters.ddcci_adapter import DdcciAdapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    ContinuousValue,
    Monitor,
    MonitorAdapter,
    NonContinuousValue,
    Property,
)
from ddcci_plasmoid_backend.cache import CacheFiles, cached_data
from ddcci_plasmoid_backend.errors import (
    MissingCacheError,
    UnsupportedPropertyValueError,
)

logger = logging.getLogger(__name__)

AdapterIdentifier = str
MonitorIdentifier = int

DetectSummary = Dict[AdapterIdentifier, Dict[MonitorIdentifier, Monitor]]

# Registry of all adapters included in this
monitor_adapter_classes: dict[AdapterIdentifier, type[MonitorAdapter]] = {
    "ddcci": DdcciAdapter
}


def _get_adapter_type(adapter: str) -> type[MonitorAdapter]:
    if adapter not in monitor_adapter_classes.keys():
        msg = f"`{adapter}` is not a valid monitor adapter type"
        raise ValueError(msg)
    return monitor_adapter_classes[adapter]


def _validate_new_property_value(
    monitor: Monitor,
    property: Property,
    value: int,
    *,
    increase_by_value: bool = False,
    constraint_to_limits,
) -> int:
    """

    Args:
        monitor:
        property:
        value:
        increase_by_value:

    Returns:

    """
    adapter = monitor["adapter"]
    id = monitor["id"]
    if property not in monitor["property_values"]:
        msg = f"Monitor `{adapter}.{id}` does not support property `{property}`"
        raise UnsupportedPropertyValueError(msg)
    if "choices" in monitor["property_values"][property]:
        property_instance: NonContinuousValue = monitor["property_values"][property]
        if increase_by_value:
            msg = f"Argument `{increase_by_value=}` is not allowed for non-continuous properties"
            raise ValueError(msg)
        if value not in property_instance["choices"]:
            msg = (
                f"Monitor `{adapter}.{id}` does not support value `{value}` for"
                f" non-continuous property `{property}`"
            )
            raise UnsupportedPropertyValueError(msg)
    else:
        property_instance: ContinuousValue = monitor["property_values"][property]
        if increase_by_value:
            value += property_instance["value"]
        if (
            value < property_instance["min_value"]
            or value > property_instance["max_value"]
        ):
            msg = (
                f"Monitor `{adapter}.{id}` does not support value `{value}` for"
                f" continuous property `{property}`"
            )
            raise UnsupportedPropertyValueError(msg)


async def detect(adapters: list[AdapterIdentifier]) -> DetectSummary:
    """
    Detect all monitors with the given adapters.

    Args:
        adapters: list of adapter identifiers, values must be equal to keys of
        `monitor_adapter_classes`.

    Returns:
        All detected monitors, mapped by adapter identifier, then by monitor identifier.
    """

    async def detect_call(
        adapter: MonitorAdapter, adapter_name: AdapterIdentifier
    ) -> DetectSummary:
        data = await adapter.detect()
        return {adapter_name: dict(data.items())}

    tasks = []
    for adapter in adapters:
        config_section = config.config[adapter]
        instance = _get_adapter_type(adapter)(config_section)
        tasks.append(asyncio.create_task(detect_call(instance, adapter)))
    result = reduce(lambda x, y: {**x, **y}, await asyncio.gather(*tasks))
    # Cache the latest detect result
    CacheFiles.DETECT.value.parent.mkdir(exist_ok=True)
    logger.info(f"Write `detect` output to cache file `{CacheFiles.DETECT.value}`")
    with CacheFiles.DETECT.value.open("w") as file:
        json.dump(result, file)
    return result


async def set_monitor_property(
    adapter: AdapterIdentifier,
    id: MonitorIdentifier,
    property_name: str,
    value: int,
    *,
    increase_by_value: bool = False,
) -> None:
    property = Property(property_name)
    monitor: Monitor
    try:
        monitor: Monitor = cached_data[CacheFiles.DETECT][adapter][str(id)]
        _validate_new_property_value(
            monitor, property, value, increase_by_value=increase_by_value
        )
        if increase_by_value:
            value += monitor["property_values"][property]["value"]
        logger.info("Property value validation succeeded")
    except KeyError as exc:
        msg = (
            f"Monitor `{adapter}.{id}` is not present in `detect` cache, cannot"
            " validate support for accessed property and assigned value"
        )
        if increase_by_value:
            # If we rely on the cache to look up the current value, do not dismiss the exception
            raise MissingCacheError(msg) from exc
        logger.warning(
            f"Monitor `{adapter}.{id}` is not present in `detect` cache, cannot"
            " validate support for accessed property and assigned value"
        )
    except UnsupportedPropertyValueError:
        msg = (
            f"Unsupported property or value found for monitor `{adapter}.{id}`,"
            f" attempt to set it anyways"
        )
        if increase_by_value:
            raise
        logger.exception(msg)

    adapter_type = _get_adapter_type(adapter)
    config_section = config.config[adapter]
    property = Property(property)
    await adapter_type(config_section).set_property(id, property, value)
    cached_data[CacheFiles.DETECT][adapter][str(id)]["property_values"][property][
        "value"
    ] = value
    with CacheFiles.DETECT.value.open("w") as file:
        json.dump(cached_data[CacheFiles.DETECT], file)


async def set_all_monitors(
    property_name: str, value: int, *, increase_by_value: bool = False
) -> None:
    property = Property(property_name)
    cached_detect_output: DetectSummary = cached_data[CacheFiles.DETECT]
    tasks = []
    for adapter, monitors in cached_detect_output.items():
        tasks.extend(
            [
                asyncio.create_task(
                    set_monitor_property(
                        adapter,
                        id,
                        property,
                        value,
                        increase_by_value=increase_by_value,
                    )
                )
                for id in monitors
            ]
        )
    await asyncio.gather(*tasks)
