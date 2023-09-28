from __future__ import annotations

import logging
import subprocess
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

from ddcci_plasmoid_backend.adapters.ddcci import (
    ddcutil_wrapper,
    detect,
)
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    Monitor,
    MonitorAdapter,
    Property,
    MonitorIdentifier,
)

if TYPE_CHECKING:
    from configparser import SectionProxy

logger = logging.getLogger(__name__)

VcpFeatureList = Dict[int, Optional[List[int]]]


class FeatureCode(Enum):
    BRIGHTNESS = 0x10
    CONTRAST = 0x12
    POWER_MODE = 0xD6


feature_code_by_property = {
    Property.BRIGHTNESS: FeatureCode.BRIGHTNESS,
    Property.CONTRAST: FeatureCode.CONTRAST,
    Property.POWER_MODE: FeatureCode.POWER_MODE,
}


class PowerModeValue(Enum):
    POWER_ON = 0x01
    DPMS_STANDBY = 0x02
    DPMS_SUSPEND = 0x03
    POWER_OFF = 0x04
    WRITE_ONLY_POWER_OFF = 0x05


class DdcciAdapter(MonitorAdapter):
    def __init__(self, config_section: SectionProxy) -> None:
        super().__init__(config_section)
        self._ddcutil_wrapper = ddcutil_wrapper.DdcutilWrapper(config_section)
        logger.info(f"ddcutil version: {self._ddcutil_wrapper.get_ddcutil_version()}")

    async def detect(self) -> dict[MonitorIdentifier, DdcciMonitor]:
        monitors = await detect.ddcutil_detect_monitors(self._ddcutil_wrapper)
        return {monitor.id: monitor for monitor in monitors}

    async def set_property(self, id: int, property: Property, value: int) -> None:
        if property not in feature_code_by_property.keys():
            msg = f"Unsupported property `{property.value}`"
            raise ValueError(msg)
        feature_code = feature_code_by_property[property]
        try:
            await self._ddcutil_wrapper.run_async(
                "setvcp", hex(feature_code.value), str(value), bus=id, logger=logger
            )
        except subprocess.CalledProcessError as err:
            msg = f"Failed to set VCP feature {feature_code.value:X} to value {value}"
            raise OSError(msg) from err


class DdcciMonitor(Monitor):
    ddcutil_id: int
    bus_id: int
    vcp_capabilities: VcpFeatureList
