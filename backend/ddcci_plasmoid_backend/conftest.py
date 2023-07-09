import pytest

from ddcci_plasmoid_backend.subprocess import CommandOutput

"""
Pytest fixtures shared throughout the entire package
"""


@pytest.fixture
def return_coroutine():
    async def inner(arg):
        return arg

    return inner


@pytest.fixture
def return_command_output():
    def inner(stdout='', stderr='', return_code=0) -> CommandOutput:
        return CommandOutput(return_code, stdout, stderr)

    return inner


@pytest.fixture
def return_callback_command_output():
    ...
