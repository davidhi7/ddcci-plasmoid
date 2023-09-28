from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, List, Dict, Union

from pydantic import BaseModel

if TYPE_CHECKING:
    from configparser import SectionProxy

AdapterIdentifier = str
MonitorIdentifier = int


class MonitorAdapter:
    def __init__(self, config_section: SectionProxy) -> None:
        self.config_section = config_section

    @abstractmethod
    async def detect(self) -> dict[MonitorIdentifier, Monitor]:
        pass

    @abstractmethod
    async def set_property(self, id: int, property: Property, value: int) -> None:
        pass


# By also inheriting from str, we can have StrEnum behaviour in earlier versions than Python 3.11
class Property(str, Enum):
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    POWER_MODE = "power_mode"

    # https://docs.astral.sh/ruff/rules/#flake8-slots-slot
    __slots__ = ()


CONTINUOUS_PROPERTIES = [Property.BRIGHTNESS, Property.CONTRAST]
NON_CONTINUOUS_PROPERTIES = [Property.POWER_MODE]


class Monitor(BaseModel):
    name: str
    adapter: AdapterIdentifier
    id: MonitorIdentifier
    property_values: Dict[Property, Union[ContinuousValue, NonContinuousValue]]


class ContinuousValue(BaseModel):
    value: int
    min_value: int
    max_value: int


class NonContinuousValue(BaseModel):
    value: int
    choices: List[int]


ContinuousValue.model_rebuild()
NonContinuousValue.model_rebuild()
Monitor.model_rebuild()
