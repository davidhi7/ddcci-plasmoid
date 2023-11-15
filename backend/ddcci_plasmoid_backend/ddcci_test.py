import json
from pathlib import Path

import pytest as pytest

from ddcci_plasmoid_backend import ddcci


@pytest.fixture
def return_CommandOutput():
    def inner(stdout="", stderr="", return_code=0) -> ddcci.CommandOutput:
        return {"stdout": stdout, "stderr": stderr, "returnCode": return_code}

    return inner


@pytest.mark.parametrize("path", Path("fixtures/detect/").glob("*"))
def test_detect(monkeypatch, path, return_CommandOutput):
    with open(path / "input.txt") as file:
        input_data = file.read()
    with open(path / "output.json") as file:
        output_data = json.load(file)

    def command_handler(cmd: str):
        if cmd.startswith("ddcutil detect"):
            return return_CommandOutput(stdout=input_data)
        return return_CommandOutput(stdout="VCP 10 C 50 100\n")

    monkeypatch.setattr(ddcci, "subprocess_wrapper", command_handler)

    assert ddcci.detect() == output_data
