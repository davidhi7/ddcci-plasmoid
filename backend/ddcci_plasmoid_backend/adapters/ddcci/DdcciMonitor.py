from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict

from ddcci_plasmoid_backend.adapters.Monitor import Monitor

VcpFeatureList = Dict[int, Optional[List[int]]]


@dataclass
class DdcciMonitor(Monitor):
    ddcutil_id: int
    bus_id: int
    vcp_capabilities: VcpFeatureList

    def prepare_json_dump(self) -> dict:
        dict = super().prepare_json_dump()
        # Replace decimal integers with hexadecimal strings
        dict['vcp_capabilities'] = {f'{code:X}': value for code, value in dict['vcp_capabilities'].items()}
        return dict
