import json
from pathlib import Path

import pytest as pytest

from ddcci_plasmoid_backend import ddcci


@pytest.fixture
def return_coroutine():
    async def inner(arg):
        return arg

    return inner


@pytest.fixture
def return_CommandOutput():
    def inner(stdout="", stderr="", return_code=0) -> ddcci.CommandOutput:
        return {"stdout": stdout, "stderr": stderr, "returnCode": return_code}

    return inner


@pytest.mark.parametrize("path", Path("fixtures/detect/").glob("*"))
async def test_detect(monkeypatch, path, return_coroutine, return_CommandOutput):
    with open(path / "input.txt") as file:
        input_data = file.read()
    with open(path / "output.json") as file:
        output_data = json.load(file)

    monkeypatch.setattr(
        ddcci, "subprocess_wrapper", lambda _: return_CommandOutput(stdout=input_data)
    )
    monkeypatch.setattr(
        ddcci,
        "async_subprocess_wrapper",
        lambda _: return_coroutine(return_CommandOutput(stdout="VCP 10 C 50 100\n")),
    )

    assert await ddcci.detect() == output_data
