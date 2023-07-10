import logging
import subprocess
from typing import Dict

from ddcci_plasmoid_backend import Property, subprocess_wrappers
from ddcci_plasmoid_backend.adapters.MonitorAdapter import MonitorAdapter
from ddcci_plasmoid_backend.adapters.ddcci import property_feature_codes
from ddcci_plasmoid_backend.adapters.ddcci.DdcciMonitor import DdcciMonitor
from ddcci_plasmoid_backend.adapters.ddcci.detect import ddcutil_detect_monitors

logger = logging.getLogger(__name__)


class DdcciAdapter(MonitorAdapter):

    def __init__(self):
        super().__init__('ddcci')

    @staticmethod
    async def detect() -> Dict[int, DdcciMonitor]:
        monitors = await ddcutil_detect_monitors()
        return {monitor.bus_id: monitor for monitor in monitors}

    @staticmethod
    async def set(property: Property, id: int, value: int) -> None:
        if property not in property_feature_codes:
            raise ValueError(f'Unsupported property `{property.value}`')
        feature_code = property_feature_codes[property]
        try:
            await subprocess_wrappers.async_subprocess_wrapper('ddcutil', 'setvcp', '--bus', f'{str(id)}',
                                                               f'{feature_code.value:x}',
                                                               f'{str(value)}', logger=logger)
        except subprocess.CalledProcessError as err:
            logger.debug(f'Failed to set VCP feature {feature_code.value:X} to value {value}')
            logger.debug(err)
