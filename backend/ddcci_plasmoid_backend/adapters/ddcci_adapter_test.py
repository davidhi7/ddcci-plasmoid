from __future__ import annotations

import json
from unittest import mock
from pathlib import Path
from typing import TYPE_CHECKING, Union

import pytest

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters import ddcci_adapter
from ddcci_plasmoid_backend.adapters.monitor_adapter import Property
from ddcci_plasmoid_backend.subprocess_wrappers import CommandOutput

if TYPE_CHECKING:
    import logging


@pytest.fixture(scope="module", params=Path("fixtures/detect/").glob("*/"))
def ddcutil_mock(request, default_command_output):  # noqa: C901
    """
    Simple mocker for ddcutil CLI that reads given command output from the following files:
    * detect.txt: raw ddcutil detect output
    * vcp.json: capabilities string and getvcp outputs by monitor, then by hexadecimal feature code
    * output.json: expected output

    Returns:
        Function with arguments program, *argv, logger to mock (async_)subprocess_wrapper and the
        parsed output.json content
    """
    # Data from json files is usually accessed in multiple calls, so let's cache it
    json_file_cache: dict[Path, dict] = {}
    fixture_dir = request.param

    def load_cached_json(path: Path):
        if path not in json_file_cache:
            with path.open() as file:
                json_file_cache[path] = json.load(file)

        return json_file_cache[path]

    # sync function that provides sample output for different ddcutil calls
    def mock(command_string: str, logger):
        command = command_string.split(" ")
        # `detect` is the only ddcutil verb that does not require or support specific monitor
        # identifications
        if "detect" in command:
            with (fixture_dir / "detect.txt").open() as file:
                return CommandOutput(stdout=file.read(), stderr="", return_code=0)

        if "--bus" in command:
            try:
                bus_id = int(command[command.index("--bus") + 1])
            except Union[ValueError, IndexError] as error:
                msg = "Failed to parse bus id of ddcutil call"
                raise ValueError(msg) from error
            if "capabilities" in command:
                return CommandOutput(
                    stdout=load_cached_json(fixture_dir / "vcp.json")[str(bus_id)][
                        "capabilities"
                    ],
                    stderr="",
                    return_code=0,
                )
            elif "getvcp" in command:  # noqa: RET505
                feature_code_index = command.index("getvcp") + 1
                if command[feature_code_index] == "--bus":
                    feature_code_index += 2
                while not command[feature_code_index].isalnum():
                    feature_code_index += 1
                try:
                    feature_code = int(command[feature_code_index], 16)
                except ValueError as error:
                    msg = "Failed to parse feature code of getvcp feature code"
                    raise ValueError(msg) from error
                return CommandOutput(
                    stdout=load_cached_json(fixture_dir / "vcp.json")[str(bus_id)][
                        f"{feature_code:X}"
                    ],
                    stderr="",
                    return_code=0,
                )
            return default_command_output
        return default_command_output

    # to replace a coroutine that is awaited, wrap the mock function in a coroutine
    async def mock_async(command: str, logger: logging.Logger):
        return mock(command, logger=logger)

    with (fixture_dir / "output.json").open() as file:
        output = json.load(file)
    return mock, mock_async, output


async def test_detect(monkeypatch, ddcutil_mock):
    sync_ddcutil_mock, async_ddcutil_mock, expected_output = ddcutil_mock
    monkeypatch.setattr(
        "ddcci_plasmoid_backend.subprocess_wrappers.subprocess_wrapper",
        sync_ddcutil_mock,
    )
    monkeypatch.setattr(
        "ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper",
        async_ddcutil_mock,
    )
    adapter = ddcci_adapter.DdcciAdapter(config.init(None)["ddcci"])
    detected_monitors = await adapter.detect()
    # turn output into only dicts
    dictified_output = {
        key: value.model_dump() for key, value in detected_monitors.items()
    }
    # JSON does not support integer keys, so dump and parse again to make sure we have valid json
    # to compare to the expected output
    json_output = json.loads(json.dumps(dictified_output))
    assert json_output == expected_output


async def test_set_basic():
    adapter = ddcci_adapter.DdcciAdapter(config.init(None)["ddcci"])
    with mock.patch.object(
        adapter._ddcutil_wrapper, "run_async", return_value=None
    ) as mocked_fn:
        await adapter.set_property(id=0, property=Property.BRIGHTNESS, value=100)
        mocked_fn.assert_called_once_with(
            "setvcp",
            hex(ddcci_adapter.FeatureCode.BRIGHTNESS.value),
            "100",
            bus=0,
            logger=ddcci_adapter.logger,
        )
