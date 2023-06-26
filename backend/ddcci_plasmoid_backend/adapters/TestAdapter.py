from ddcci_plasmoid_backend import Property
from ddcci_plasmoid_backend.adapters.Monitor import Monitor, ContinuousValue
from ddcci_plasmoid_backend.adapters.MonitorAdapter import MonitorAdapter


class TestAdapter(MonitorAdapter):

    def __init__(self):
        super().__init__('test')

    @staticmethod
    async def detect():
        return {
            1: Monitor(name='test1', property_values={Property.BRIGHTNESS: ContinuousValue(value=50, min=0, max=100)}),
            2: Monitor(name='test1', property_values={Property.BRIGHTNESS: ContinuousValue(value=50, min=0, max=100)})
        }

    @staticmethod
    async def set(property: Property, id: int, value: int):
        pass
