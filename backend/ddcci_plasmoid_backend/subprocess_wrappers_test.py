from __future__ import annotations

import inspect

import pytest

from ddcci_plasmoid_backend import subprocess_wrappers
from ddcci_plasmoid_backend.subprocess_wrappers import CalledProcessError


@pytest.mark.parametrize(
    "subprocess_method",
    [
        subprocess_wrappers.subprocess_wrapper,
        subprocess_wrappers.async_subprocess_wrapper,
    ],
)
async def test_subprocess_wrapper_success(silent_logger, subprocess_method):
    return_value = subprocess_method(
        "python -c \"import os; os.write(1, b'test-stdout'); os.write(2,"
        " b'test-stderr')\"",
        logger=silent_logger,
    )
    output = await return_value if inspect.isawaitable(return_value) else return_value
    assert output.stdout == "test-stdout"
    assert output.stderr == "test-stderr"
    assert output.return_code == 0


@pytest.mark.parametrize(
    "subprocess_method",
    [
        subprocess_wrappers.subprocess_wrapper,
        subprocess_wrappers.async_subprocess_wrapper,
    ],
)
async def test_subprocess_wrapper_fail(silent_logger, subprocess_method):
    # /usr/bin/false will always return a return code of 1
    # Second and third statement is required to allow conditional awaiting
    with pytest.raises(CalledProcessError):  # noqa: PT012
        return_value = subprocess_method("false", logger=silent_logger)
        if inspect.isawaitable(return_value):
            await return_value
