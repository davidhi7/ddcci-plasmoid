import asyncio
from typing import List, Dict
from functools import reduce

from ddcci_plasmoid_backend import Property
from ddcci_plasmoid_backend.adapters.MonitorAdapter import MonitorAdapter
from ddcci_plasmoid_backend.adapters.TestAdapter import TestAdapter
from ddcci_plasmoid_backend.adapters.DdcciAdapter import DdcciAdapter

# Registration of all adapters included in this
monitor_adapters = [
    DdcciAdapter(),
    TestAdapter()
]


def adapter_by_label(label: str) -> 'MonitorAdapter':
    for backend in monitor_adapters:
        if label == backend.label:
            return backend
    raise ValueError(f'Invalid backend label `{label}`')


async def detect(adapters: List[MonitorAdapter]) -> Dict[str, Dict]:
    async def detect_call(adapter: MonitorAdapter):
        data = await adapter.detect()
        return {
            adapter.label: {key: monitor.prepare_json_dump() for key, monitor in data.items()}
        }

    tasks = []
    for adapter in adapters:
        tasks.append(asyncio.create_task(detect_call(adapter)))
    #
    result = await asyncio.gather(*tasks)
    return reduce(lambda x, y: {**x, **y}, result)


def set_property(adapter: MonitorAdapter, property: Property, id: int, value: int):
    return adapter.set(property, id, value)
