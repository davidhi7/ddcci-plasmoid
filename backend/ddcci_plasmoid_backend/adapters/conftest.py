from __future__ import annotations

from pytest_asyncio import fixture

from ddcci_plasmoid_backend.subprocess_wrappers import CommandOutput


@fixture(scope="module")
def default_command_output():
    return CommandOutput(0, "", "")
