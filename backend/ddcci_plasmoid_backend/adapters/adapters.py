from __future__ import annotations

import asyncio
import json
import logging
from functools import reduce
from typing import Dict

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters.ddcci_adapter import DdcciAdapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    AdapterIdentifier,
    ContinuousValue,
    Monitor,
    MonitorAdapter,
    MonitorIdentifier,
    Property,
)
from ddcci_plasmoid_backend.cache import CacheFiles, cached_data
from ddcci_plasmoid_backend.errors import (
    IllegalPropertyValueError,
    MissingCacheError,
    UnsupportedPropertyError,
)

logger = logging.getLogger(__name__)


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


def _validate_non_continuous_property_value(
    monitor: Monitor, property: Property, value: int
) -> bool:
    """Check whether `value` is an accepted value for the non-continuous property `property` of the
    monitor `monitor`.

    Args:
        monitor: Monitor instance
        property: Monitor property
        value: Value to check

    Returns:
        `True` if `value` is accepted, otherwise `False`
    """
    return value in monitor.property_values[property].choices


def _limit_continuous_property_value(
    monitor: Monitor, property: Property, value: int, increase_by_value: True
) -> int:
    """Transform `value` into an accepted value for the continuous property `property` of the
    monitor `monitor`. If `value` is greater than or lesser than the min/max value,
    apply the respective limiting value.

    Args:
        monitor: Monitor instance
        property: Monitor Property
        value: Value to transform
        increase_by_value: If `True`, add `value` to the current monitor property value.

    Returns:
        Transformed `value`
    """
    property_instance: ContinuousValue = monitor.property_values[property]
    if increase_by_value:
        value += property_instance.value
    if value < property_instance.min_value:
        return property_instance.min_value
    if value > property_instance.max_value:
        return property_instance.max_value
    return value


async def detect(adapters: list[AdapterIdentifier]) -> DetectSummary:
    """
    Detect all monitors with the given adapters.

    Args:
        adapters: list of adapter identifiers, values must be equal to keys of
        `monitor_adapter_classes`.

    Returns:
        All detected monitors, mapped by adapter identifier, then by monitor identifier.
    """

    async def call_adapter(
        adapter: MonitorAdapter, adapter_name: AdapterIdentifier
    ) -> DetectSummary:
        data = await adapter.detect()
        return {adapter_name: dict(data.items())}

    tasks = []
    for adapter in adapters:
        config_section = config.config[adapter]
        adapter_instance = _get_adapter_type(adapter)(config_section)
        tasks.append(asyncio.create_task(call_adapter(adapter_instance, adapter)))
    result = reduce(lambda x, y: {**x, **y}, await asyncio.gather(*tasks))
    # Cache the latest detect result
    logger.info(f"Write `detect` output to cache file `{CacheFiles.DETECT.value}`")
    CacheFiles.DETECT.value.parent.mkdir(exist_ok=True)
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
) -> int:
    property = Property(property_name)
    monitor: Monitor | None = None
    try:
        monitor = Monitor.model_validate(
            cached_data[CacheFiles.DETECT][adapter][str(id)]
        )
    except KeyError as exc:
        msg = (
            f"Monitor `{adapter}.{id}` is not present in `detect` cache, cannot"
            " validate support for accessed property and assigned value"
        )
        if increase_by_value:
            # If we rely on the cache to look up the current value, do not dismiss the exception
            raise MissingCacheError(msg) from exc
        # Otherwise just skip validation
        logger.warning(msg)

    if isinstance(monitor, Monitor):
        if property not in monitor.property_values.keys():
            raise UnsupportedPropertyError(monitor.adapter, monitor.id, property)

        property_instance = monitor.property_values[property]
        if isinstance(property_instance, ContinuousValue):
            value = _limit_continuous_property_value(
                monitor, property, value, increase_by_value
            )
        elif not _validate_non_continuous_property_value(monitor, property, value):
            raise IllegalPropertyValueError(
                monitor.adapter, monitor.id, property, value, is_continuous=False
            )
        logger.info("Property value validation succeeded")
    else:
        logger.warning(
            "Property value validation skipped because no cache is available"
        )
    config_section = config.config[adapter]
    adapter_instance = _get_adapter_type(adapter)(config_section)
    await adapter_instance.set_property(id, property, value)
    # Write the new values to the cache
    cached_data[CacheFiles.DETECT][adapter][str(id)]["property_values"][property][
        "value"
    ] = value
    with CacheFiles.DETECT.value.open("w") as file:
        json.dump(cached_data[CacheFiles.DETECT], file)
    return value


async def set_all_monitors(
    property_name: str, value: int, *, increase_by_value: bool = False
) -> dict[AdapterIdentifier, dict[MonitorIdentifier, int]]:
    # TODO right argument
    cached_detect_output: DetectSummary = cached_data[CacheFiles.DETECT]
    tasks = []
    for adapter, monitors in cached_detect_output.items():
        tasks.extend(
            [
                asyncio.create_task(
                    set_monitor_property(
                        adapter,
                        id,
                        property_name,
                        value,
                        increase_by_value=increase_by_value,
                    )
                )
                for id in monitors
            ]
        )
    await asyncio.gather(*tasks)
