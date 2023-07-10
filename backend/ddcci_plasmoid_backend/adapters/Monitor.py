from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum


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
    choices: list[int]


@dataclass
class Monitor:
    name: str
    property_values: dict[Property, ContinuousValue | NonContinuousValue]

    def prepare_json_dump(self) -> dict:
        dict_representation = dataclasses.asdict(self)
        dict_representation['property_values'] = \
            {property.value: value for property, value in dict_representation['property_values'].items()}
        return dict_representation
