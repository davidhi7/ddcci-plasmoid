from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class Property(Enum):
    BRIGHTNESS = 'brightness'
    CONTRAST = 'contrast'
    POWER_MODE = 'power_mode'


@dataclass
class ContinuousValue:
    value: int
    min: int
    max: int


@dataclass
class NonContinuousValue:
    value: int
    choices: List[int]


@dataclass
class Monitor:
    name: str
    property_values: Dict[Property, ContinuousValue | NonContinuousValue]

    def prepare_json_dump(self) -> Dict:
        dict_representation = dataclasses.asdict(self)
        dict_representation['property_values'] = \
            {property.value: value for property, value in dict_representation['property_values'].items()}
        return dict_representation
