from dataclasses import dataclass
from typing import Dict, Optional, List

from ddcci_plasmoid_backend.adapters.Monitor import Monitor

VcpFeatureList = Dict[int, Optional[List[int]]]


@dataclass
class DdcciMonitor(Monitor):
    ddcutil_id: int
    bus_id: int
    vcp_capabilities: VcpFeatureList

    def prepare_json_dump(self) -> Dict:
        dict = super().prepare_json_dump()
        # Replace decimal integers with hexadecimal strings
        dict['vcp_capabilities'] = {f'{code:X}': value for code, value in dict['vcp_capabilities'].items()}
        return dict
