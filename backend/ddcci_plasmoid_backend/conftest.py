import logging

import pytest

from ddcci_plasmoid_backend.subprocess_wrappers import CommandOutput

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
    def inner(stdout="", stderr="", return_code=0, *args, **kwargs) -> CommandOutput:
        return CommandOutput(return_code, stdout, stderr)

    return inner


@pytest.fixture
def silent_logger():
    logger = logging.getLogger("silent_logger")
    logger.setLevel(logging.CRITICAL + 1)
    return logger
