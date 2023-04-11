import json
from pathlib import Path
from typing import Callable, Any, Coroutine

import pytest as pytest

from ddcci_plasmoid_backend import ddcci


@pytest.fixture
def detect_mock() -> Callable[[Path], ddcci.CommandOutput]:
    def inner(path: Path) -> ddcci.CommandOutput:
        with open(path, 'r') as file:
            return {
                'stdout': file.read(),
                'stderr': '',
                'returnCode': 0
            }

    return inner


@pytest.fixture
def return_coroutine():
    async def inner(arg):
        return arg

    return inner


@pytest.fixture
def return_CommandOutput():
    def inner(stdout='', stderr='', return_code=0) -> ddcci.CommandOutput:
        return {
            'stdout': stdout,
            'stderr': stderr,
            'returnCode': return_code
        }

    return inner


@pytest.mark.parametrize('dir', [
    'fixtures/detect/simple', 'fixtures/detect/duplicate', 'fixtures/detect/#1-wrong-duplicates',
    'fixtures/detect/duplicate-binary-serial-numbers'
])
async def test_detect(monkeypatch, dir, return_coroutine, return_CommandOutput):
    path = Path(dir)
    with open(path / 'input.txt') as file:
        input_data = file.read()
    with open(path / 'output.json') as file:
        output_data = json.load(file)

    monkeypatch.setattr(ddcci, 'subprocess_wrapper', lambda _: return_CommandOutput(stdout=input_data))
    monkeypatch.setattr(ddcci, 'async_subprocess_wrapper',
                        lambda _: return_coroutine(return_CommandOutput(stdout='VCP 10 C 50 100')))

    report = await ddcci.detect()
    print(report)
    print(output_data)
    assert report == output_data


@pytest.fixture
def getvcp_brightness_mock() -> Callable[[], Coroutine[Any, Any, ddcci.CommandOutput]]:
    async def inner() -> ddcci.CommandOutput:
        # return constant value of 50
        return {
            'stdout': 'VCP 10 C 50 100',
            'stderr': '',
            'returnCode': 0
        }

    return inner

# @pytest.mark.asyncio
# async def test_detect_default(monkeypatch, detect_mock, getvcp_brightness_mock):
#     monkeypatch.setattr(ddcci, 'subprocess_wrapper', lambda _: detect_mock(Path('fixtures/detect/basic.txt')))
#     monkeypatch.setattr(ddcci, 'async_subprocess_wrapper', lambda _: getvcp_brightness_mock())
#
#     assert await ddcci.detect() == [
#         {
#             'id': 1,
#             'name': 'DELL S2721DGF',
#             'bus_id': 9,
#             'brightness': 50
#         }, {
#             'id': 2,
#             'name': 'DELL U2417H',
#             'bus_id': 10,
#             'brightness': 50
#         }
#     ]
