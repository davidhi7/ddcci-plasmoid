from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from configparser import SectionProxy

    from ddcci_plasmoid_backend.adapters.adapters import (
        MonitorIdentifier,
        AdapterIdentifier,
    )


class MonitorAdapter:
    def __init__(self, config_section: SectionProxy) -> None:
        self.config_section = config_section

    @abstractmethod
    async def detect(self) -> dict[MonitorIdentifier, Monitor]:
        pass

    @abstractmethod
    async def set_property(self, id: int, property: Property, value: int) -> None:
        pass


class Monitor(TypedDict):
    name: str
    adapter: AdapterIdentifier
    id: MonitorIdentifier
    property_values: dict[Property, ContinuousValue | NonContinuousValue]


# By also inheriting from str, we can have StrEnum behaviour in earlier versions than Python 3.11
class Property(str, Enum):
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    POWER_MODE = "power_mode"

    # https://docs.astral.sh/ruff/rules/#flake8-slots-slot
    __slots__ = ()


CONTINUOUS_PROPERTIES = [Property.BRIGHTNESS, Property.CONTRAST]
NON_CONTINUOUS_PROPERTIES = [Property.POWER_MODE]


class ContinuousValue(TypedDict):
    value: int
    min_value: int
    max_value: int


class NonContinuousValue(TypedDict):
    value: int
    choices: list[int]
