from __future__ import annotations

import asyncio
from functools import reduce
from typing import Dict

from ddcci_plasmoid_backend.adapters.ddcci_adapter import DdcciAdapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    Monitor,
    MonitorAdapter,
    Options,
    Property,
)
from ddcci_plasmoid_backend.default_options import DEFAULT_OPTIONS

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


def _merge_default_options(options: Options) -> Options:
    return {**DEFAULT_OPTIONS, **options}


async def detect(adapters: list[AdapterIdentifier], options: Options) -> DetectSummary:
    """
    Detect all monitors with the given adapters.

    Args:
        adapters: list of adapter identifiers, values must be equal to keys of `monitor_adapter_classes`.
        options: Custom options to override default options with.

    Returns:
        All detected monitors, mapped by adapter identifier, then by monitor identifier.
    """

    async def detect_call(adapter: MonitorAdapter, label: str) -> DetectSummary:
        data = await adapter.detect()
        return {
            label: {key: monitor.prepare_json_dump() for key, monitor in data.items()}
        }

    tasks = []
    options = _merge_default_options(options)
    for adapter in adapters:
        instance = _get_adapter_type(adapter)(options)
        tasks.append(asyncio.create_task(detect_call(instance, adapter)))
    result = await asyncio.gather(*tasks)
    return reduce(lambda x, y: {**x, **y}, result)


async def set_property(
        adapter: str, options: Options, property: str, id: int, value: int
) -> None:
    adapter_type = _get_adapter_type(adapter)
    merged_options = _merge_default_options(options)
    property = Property(property)
    return await adapter_type(merged_options).set_property(property, id, value)
