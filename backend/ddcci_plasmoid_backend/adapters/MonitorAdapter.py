from abc import abstractmethod
from dataclasses import dataclass

from ddcci_plasmoid_backend import Property


@dataclass
class MonitorAdapter:
    label: str

    @staticmethod
    @abstractmethod
    async def detect():
        pass

    @staticmethod
    @abstractmethod
    async def set(property: Property, id: int, value: int):
        pass
