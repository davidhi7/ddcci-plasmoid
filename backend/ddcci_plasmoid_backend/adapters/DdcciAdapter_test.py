from __future__ import annotations

import json
from pathlib import Path

import pytest

from ddcci_plasmoid_backend import subprocess
from ddcci_plasmoid_backend.adapters.DdcciAdapter import DdcciAdapter
from ddcci_plasmoid_backend.subprocess import CommandOutput


@pytest.fixture(scope='module', params=Path('fixtures/detect/').glob('*/'))
def ddcutil_mock(request):
    """
    Simple mocker for ddcutil CLI that reads given command output from the following files:
    * detect.txt: raw ddcutil detect output
    * vcp.json: capabilities string and getvcp outputs by monitor, then by hexadecimal feature code
    * output.json: expected output

    Returns:
        Function with arguments program, *argv, logger to mock (async_)subprocess_wrapper and the parsed output.json
        content
    """
    # Data from json files is usually accessed in multiple calls, so let's cache it
    json_file_cache = {}
    fixture_dir = request.param

    def load_cached_json(path):
        if path not in json_file_cache:
            with open(path, 'r') as file:
                print('file loaded')
                json_file_cache[path] = json.load(file)

        return json_file_cache[path]

    def mock(*command: str, logger):
        # `detect` is the only ddcutil verb that does not require or support specific monitor identifications
        if 'detect' in command:
            with open(fixture_dir / 'detect.txt') as file:
                return CommandOutput(stdout=file.read(), stderr='', returnCode=0)

        if '--bus' in command:
            try:
                bus_id = int(command[command.index('--bus') + 1])
            except ValueError | IndexError:
                raise ValueError('Failed to parse bus id of ddcutil call')
            if 'capabilities' in command:
                return CommandOutput(stdout=load_cached_json(fixture_dir / 'vcp.json')[str(bus_id)]['capabilities'],
                                     stderr='', returnCode=0)
            elif 'getvcp' in command:
                feature_code_index = command.index('getvcp') + 1
                if command[feature_code_index] == '--bus':
                    feature_code_index += 2
                while not command[feature_code_index].isalnum():
                    feature_code_index += 1
                try:
                    feature_code = int(command[feature_code_index], 16)
                except ValueError:
                    raise ValueError('Failed to parse feature code of getvcp feature code')
                return CommandOutput(
                    stdout=load_cached_json(fixture_dir / 'vcp.json')[str(bus_id)][f'{feature_code:X}'],
                    stderr='',
                    returnCode=0
                )

    with open(fixture_dir / 'output.json') as file:
        output = json.load(file)
    return mock, output


@pytest.fixture(scope='module')
def async_ddcutil_mock(ddcutil_mock):
    mock, _ = ddcutil_mock

    async def inner(*command, logger):
        return mock(*command, logger=logger)

    return inner


async def test_detect(monkeypatch, ddcutil_mock, async_ddcutil_mock):
    sync_ddcutil_mock, expected_output = ddcutil_mock
    monkeypatch.setattr(subprocess, 'subprocess_wrapper', sync_ddcutil_mock)
    monkeypatch.setattr(subprocess, 'async_subprocess_wrapper', async_ddcutil_mock)
    detected_monitors = await DdcciAdapter.detect()
    # turn output into only dicts
    dictified_output = {key: value.prepare_json_dump() for key, value in detected_monitors.items()}
    # JSON does not support integer keys, so dump and parse again to make sure we have valid json to compare to the
    # expected output
    json_output = json.loads(json.dumps(dictified_output))
    assert json_output == expected_output


