import pytest

from ddcci_plasmoid_backend.subprocess_wrapper import CommandOutput

"""
Pytest fixtures shared throughout the entire package
"""


@pytest.fixture
def return_coroutine():
    async def inner(arg):
        print('here')
        return arg

    return inner


@pytest.fixture
def return_CommandOutput():
    def inner(stdout='', stderr='', return_code=0) -> CommandOutput:
        return CommandOutput(return_code, stdout, stderr)

    return inner
