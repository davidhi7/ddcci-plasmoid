from pytest_asyncio import fixture

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters.ddcci.ddcutil_wrapper import DdcutilWrapper


@fixture
def default_ddcutil_wrapper():
    return DdcutilWrapper(config.init(None)["ddcci"])
