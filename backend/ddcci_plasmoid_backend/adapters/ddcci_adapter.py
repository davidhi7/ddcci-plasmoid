from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from ddcci_plasmoid_backend.adapters.adapters import MonitorIdentifier
from ddcci_plasmoid_backend.adapters.ddcci import (
    ddcutil_wrapper,
    detect,
)
from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    Monitor,
    MonitorAdapter,
    Options,
    Property,
)

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


class PowerModeValues(Enum):
    POWER_ON = 0x01
    DPMS_STANDBY = 0x02
    DPMS_SUSPEND = 0x03
    POWER_OFF = 0x04
    WRITE_ONLY_POWER_OFF = 0x05


class DdcciAdapter(MonitorAdapter):
    def __init__(self, options: Options) -> None:
        super().__init__(options)
        self._ddcutil_wrapper = ddcutil_wrapper.DdcutilWrapper(options)
        logger.info(f"ddcutil version: {self._ddcutil_wrapper.get_ddcutil_version()}")

    async def detect(self) -> dict[MonitorIdentifier, DdcciMonitor]:
        monitors = await detect.ddcutil_detect_monitors(self._ddcutil_wrapper)
        return {monitor.bus_id: monitor for monitor in monitors}

    async def set_property(self, property: Property, id: int, value: int) -> None:
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


@dataclass
class DdcciMonitor(Monitor):
    ddcutil_id: int
    bus_id: int
    vcp_capabilities: VcpFeatureList

    def prepare_json_dump(self) -> dict:
        dump = super().prepare_json_dump()
        # Replace decimal integers with hexadecimal strings
        dump["vcp_capabilities"] = {
            f"{code:X}": value for code, value in dump["vcp_capabilities"].items()
        }
        return dump
