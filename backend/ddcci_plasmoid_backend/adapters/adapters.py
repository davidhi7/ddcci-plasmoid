from __future__ import annotations

import asyncio
from functools import reduce
from typing import Dict

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters.ddcci_adapter import DdcciAdapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    Monitor,
    MonitorAdapter,
    Property,
)

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


async def detect(adapters: list[AdapterIdentifier]) -> DetectSummary:
    """
    Detect all monitors with the given adapters.

    Args:
        adapters: list of adapter identifiers, values must be equal to keys of `monitor_adapter_classes`.

    Returns:
        All detected monitors, mapped by adapter identifier, then by monitor identifier.
    """

    async def detect_call(adapter: MonitorAdapter, label: str) -> DetectSummary:
        data = await adapter.detect()
        return {
            label: {key: monitor.prepare_json_dump() for key, monitor in data.items()}
        }

    tasks = []
    for adapter in adapters:
        config_section = config.config[adapter]
        instance = _get_adapter_type(adapter)(config_section)
        tasks.append(asyncio.create_task(detect_call(instance, adapter)))
    result = await asyncio.gather(*tasks)
    return reduce(lambda x, y: {**x, **y}, result)


async def set_property(adapter: str, property: str, id: int, value: int) -> None:
    adapter_type = _get_adapter_type(adapter)
    config_section = config.config[adapter]
    property = Property(property)
    return await adapter_type(config_section).set_property(property, id, value)
