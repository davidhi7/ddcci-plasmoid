from __future__ import annotations

import dataclasses
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configparser import SectionProxy

    from ddcci_plasmoid_backend.adapters.adapters import MonitorIdentifier


class MonitorAdapter:
    def __init__(self, config_section: SectionProxy) -> None:
        self.config_section = config_section

    @abstractmethod
    async def detect(self) -> dict[MonitorIdentifier, Monitor]:
        pass

    @abstractmethod
    async def set_property(self, property: Property, id: int, value: int) -> None:
        pass


@dataclass
class Monitor:
    name: str
    property_values: dict[Property, ContinuousValue | NonContinuousValue]

    def prepare_json_dump(self) -> dict:
        dict_representation = dataclasses.asdict(self)
        dict_representation["property_values"] = {
            property.value: value
            for property, value in dict_representation["property_values"].items()
        }
        return dict_representation


class Property(Enum):
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    POWER_MODE = "power_mode"


@dataclass
class ContinuousValue:
    value: int
    min_value: int
    max_value: int


@dataclass
class NonContinuousValue:
    value: int
    choices: list[int]
