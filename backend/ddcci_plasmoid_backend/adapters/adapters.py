from __future__ import annotations

import asyncio
import json
import logging
from functools import reduce
from typing import Dict

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters.ddcci_adapter import DdcciAdapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    Monitor,
    MonitorAdapter,
    Property,
)
from ddcci_plasmoid_backend.cache import CacheFiles

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


async def detect(adapters: list[AdapterIdentifier]) -> DetectSummary:
    """
    Detect all monitors with the given adapters.

    Args:
        adapters: list of adapter identifiers, values must be equal to keys of
        `monitor_adapter_classes`.

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
    result = reduce(lambda x, y: {**x, **y}, await asyncio.gather(*tasks))
    # Cache the latest detect result
    CacheFiles.DETECT.value.parent.mkdir(exist_ok=True)
    logger.info(f"Write `detect` output to cache file `{CacheFiles.DETECT.value}`")
    with CacheFiles.DETECT.value.open("w") as file:
        json.dump(result, file)
    return result


async def set_property(adapter: str, property: str, id: int, value: int) -> None:
    adapter_type = _get_adapter_type(adapter)
    config_section = config.config[adapter]
    property = Property(property)
    return await adapter_type(config_section).set_property(property, id, value)


async def set_all_monitors(property: str, value: int) -> None:
    if not CacheFiles.DETECT.value.is_file():
        msg = f"Cache file `{CacheFiles.DETECT.value}` is not a file"
        raise FileNotFoundError(msg)
    property = Property(property)
    cache: DetectSummary
    with CacheFiles.DETECT.value.open() as file:
        cache = json.load(file)
    tasks = []
    for adapter, monitors in cache.items():
        for id in monitors:
            tasks.append(
                asyncio.create_task(
                    _get_adapter_type(adapter)(config.config[adapter]).set_property(
                        property, id, value
                    )
                )
            )
    await asyncio.gather(*tasks)
