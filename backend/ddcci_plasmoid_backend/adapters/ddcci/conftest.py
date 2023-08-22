from pytest_asyncio import fixture

from ddcci_plasmoid_backend.adapters.ddcci.ddcutil_wrapper import DdcutilWrapper
from ddcci_plasmoid_backend.default_options import DEFAULT_OPTIONS


@fixture
def default_ddcutil_wrapper():
    return DdcutilWrapper(DEFAULT_OPTIONS)
