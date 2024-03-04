from __future__ import annotations

import asyncio
import itertools
import logging
from functools import reduce
from typing import Callable, Dict

from ddcci_plasmoid_backend import cache, config
from ddcci_plasmoid_backend.adapters.ddcci_adapter import DdcciAdapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    AdapterIdentifier,
    ContinuousValue,
    Monitor,
    MonitorAdapter,
    MonitorIdentifier,
    NonContinuousValue,
    Property,
)
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
    if property not in monitor.property_values:
        raise UnsupportedPropertyError(monitor.adapter, monitor.id, property)
    return value in monitor.property_values[property].choices


def _limit_continuous_property_value(
    monitor: Monitor, property: Property, value: int
) -> int:
    """Transform `value` into an accepted value for the continuous property `property` of the
    monitor `monitor`. If `value` is greater than or lesser than the min/max value,
    apply the respective limiting value.

    Args:
        monitor: Monitor instance
        property: Monitor Property
        value: Value to transform

    Returns:
        New `value`
    """
    if property not in monitor.property_values:
        raise UnsupportedPropertyError(monitor.adapter, monitor.id, property)
    property_instance: ContinuousValue = monitor.property_values[property]
    return min(
        max(value, property_instance.min_value),
        property_instance.max_value,
    )


def _ensure_valid_property_value(
    monitor: Monitor, property: Property, value: int
) -> int:
    """Ensure a value is valid for a monitor property. For continuous properties, limit the value to
    the min/max value if it is lesser/greater. For non-continuouos properties, raise a
    `IllegalPropertyValueError` if the value is not a valid choice.

    Args:
        monitor: Monitor instance
        property: Monitor property
        value: Value to validate and limit

    Returns:
        Validated `value`, or the nearest accepted value if `property` is a continuous property and
        `value` was too great or little before.
    """
    if property not in monitor.property_values:
        raise UnsupportedPropertyError(monitor.adapter, monitor.id, property)
    if isinstance(monitor.property_values[property], NonContinuousValue):
        if not _validate_non_continuous_property_value(monitor, property, value):
            raise IllegalPropertyValueError(
                monitor.adapter, monitor.id, property, value
            )
        return value
    return _limit_continuous_property_value(monitor, property, value)


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
    result = cache.DetectOutput.model_validate(
        {"data": reduce(lambda x, y: {**x, **y}, await asyncio.gather(*tasks))}
    )
    # Cache the latest detect result
    logger.info(
        f"Write `detect` output to cache file `{cache.CacheFile.DETECT_OUTPUT.value.path}`"
    )
    cache.cached_data[cache.CacheFile.DETECT_OUTPUT] = result
    cache.write_cache_file(cache.CacheFile.DETECT_OUTPUT)
    return result.model_dump()["data"]


async def set_monitor_property(
    adapter: AdapterIdentifier,
    id: MonitorIdentifier,
    property_name: str,
    value: int | Callable[[Monitor, Property], int],
) -> int:
    """Assigns a new value to a monitor property. If the monitor is present in the cache, new value
    is validated against the min/max accepted values or the accepted choices, respectively.

    Args:
        adapter: Adapter identification
        id: Monitor identification
        property_name: String representation of the property
        value: Either a new integer value or a callback that accepts the monitor instance and
            property and returns a new value

    Returns:
        New integer value
    """
    property = Property(property_name)
    monitor: Monitor | None = None
    try:
        cached_monitors: cache.DetectOutput = cache.cached_data[
            cache.CacheFile.DETECT_OUTPUT
        ]
        monitor = Monitor.model_validate(cached_monitors.data[adapter][id])
        if isinstance(value, Callable):
            value = value(monitor, property)
    except KeyError as exc:
        msg = (
            f"Monitor `{adapter}.{id}` is not present in `detect` cache, cannot"
            " validate support for accessed property and assigned value"
        )
        if isinstance(value, Callable):
            # If we rely on the cache to compute up the current value, do not dismiss the exception
            raise MissingCacheError(msg) from exc
        # Otherwise just skip validation
        logger.warning(msg)

    if isinstance(monitor, Monitor):
        if property not in monitor.property_values.keys():
            raise UnsupportedPropertyError(monitor.adapter, monitor.id, property)

        property_instance = monitor.property_values[property]
        if isinstance(property_instance, ContinuousValue):
            value = _limit_continuous_property_value(monitor, property, value)
        elif not _validate_non_continuous_property_value(monitor, property, value):
            raise IllegalPropertyValueError(
                monitor.adapter, monitor.id, property, value
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
    if monitor is not None:
        monitor.property_values[property].value = value
        cache.write_cache_file(cache.CacheFile.DETECT_OUTPUT)
    return value


async def set_all_monitors(
    property_name: str, value: int | Callable[[list[Monitor], Property], int]
) -> int:
    """Assigns a new value to all monitors. Requires DETECT_OUTPUT cache.

    Args:
        property_name: String representation of the property
        value: Either a new integer value or a callback that accepts a list of all monitor instances
            and the property and returns a new value. In either case, the new value is used for all
            found monitors.

    Returns:
        New integer value
    """
    # TODO handle errors during setvcp
    property = Property(property_name)
    try:
        cached_detect_output: cache.DetectOutput = cache.cached_data[
            cache.CacheFile.DETECT_OUTPUT
        ]
    except KeyError as exc:
        raise MissingCacheError(cache.CacheFile.DETECT_OUTPUT) from exc

    monitors_by_adapter: dict[AdapterIdentifier, list[Monitor]] = {}
    for adapter, monitor_dict in cached_detect_output.data.items():
        monitors_by_adapter[adapter] = list(monitor_dict.values())
    if isinstance(value, Callable):
        value = value(
            list(itertools.chain.from_iterable(monitors_by_adapter.values())), property
        )

    tasks = []
    for adapter, monitor_list in monitors_by_adapter.items():
        config_section = config.config[adapter]
        adapter_instance = _get_adapter_type(adapter)(config_section)
        for monitor in monitor_list:
            monitor_specific_value = value
            try:
                monitor_specific_value = _ensure_valid_property_value(
                    monitor, property, value
                )
                monitor.property_values[property].value = monitor_specific_value
            except IllegalPropertyValueError:
                logger.exception(
                    f"{adapter}.{monitor.id}: Illegal value {value} for property {property}, try to set it"
                    f" regardless"
                )
            task = asyncio.create_task(
                adapter_instance.set_property(
                    monitor.id,
                    property,
                    monitor_specific_value,
                )
            )
            tasks.append(task)

    await asyncio.gather(*tasks)
    cache.write_cache_file(cache.CacheFile.DETECT_OUTPUT)
    return value
