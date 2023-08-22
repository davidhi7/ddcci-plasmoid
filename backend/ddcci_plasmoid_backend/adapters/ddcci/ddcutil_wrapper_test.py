from unittest import mock
from unittest.mock import MagicMock, call

import pytest
from pytest_asyncio import fixture

from ddcci_plasmoid_backend.adapters.ddcci.ddcutil_wrapper import DdcutilWrapper
from ddcci_plasmoid_backend.default_options import DEFAULT_OPTIONS
from ddcci_plasmoid_backend.subprocess_wrappers import CalledProcessError, CommandOutput


@fixture(scope='function')
def mock_subprocess_wrapper(default_command_output):
    with mock.patch('ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper',
                    return_value=default_command_output) as mocked_function:
        yield mocked_function


@fixture(params=['detect', 'capabilities', 'getvcp', 'setvcp'])
def ddcutil_verbs(request):
    return request.param


async def test_basic_functionality(silent_logger, default_ddcutil_wrapper, ddcutil_verbs,
                                   mock_subprocess_wrapper: MagicMock,
                                   default_command_output):
    assert await default_ddcutil_wrapper.run_async(ddcutil_verbs, 'arg1', 'arg2', bus=0,
                                                   logger=silent_logger) == default_command_output
    mock_subprocess_wrapper.assert_called_once_with(
        f'ddcutil {"--bus 0 " if ddcutil_verbs != "detect" else ""}{ddcutil_verbs} arg1 arg2', silent_logger)


async def test_detect_bus_error(silent_logger, default_ddcutil_wrapper, ddcutil_verbs,
                                mock_subprocess_wrapper: MagicMock):
    if ddcutil_verbs != 'detect':
        with pytest.raises(ValueError):
            await default_ddcutil_wrapper.run_async(ddcutil_verbs, logger=silent_logger)


async def test_sleep_multiplier(silent_logger, ddcutil_verbs, mock_subprocess_wrapper: MagicMock):
    custom_options = dict(DEFAULT_OPTIONS)
    custom_options['ddcutil_sleep_multiplier'] = 1.5
    ddcutil_wrapper = DdcutilWrapper(custom_options)
    await ddcutil_wrapper.run_async(ddcutil_verbs, 'arg1', bus=0, logger=silent_logger)
    mock_subprocess_wrapper.assert_called_once_with(
        f'ddcutil {"--bus 0 " if ddcutil_verbs != "detect" else ""}--sleep-multiplier 1.5 {ddcutil_verbs} arg1',
        silent_logger
    )


async def test_no_verify(silent_logger, mock_subprocess_wrapper: MagicMock):
    custom_options = dict(DEFAULT_OPTIONS)
    custom_options['ddcutil_no_verify'] = True
    ddcutil_wrapper = DdcutilWrapper(custom_options)
    await ddcutil_wrapper.run_async('setvcp', 'arg1', bus=0, logger=silent_logger)
    mock_subprocess_wrapper.assert_called_once_with('ddcutil --bus 0 setvcp --noverify arg1', silent_logger)


@pytest.mark.parametrize('erroneous_attempts', [6, 3])
async def test_brute_force_attempts(silent_logger, ddcutil_verbs, default_command_output, erroneous_attempts):
    erroneous_command_output = CommandOutput(stdout='DDC communication failed', stderr='', return_code=0)

    class ErroneousAttemptProvider:
        """
        Implement a solution that provides CommandOutput instances that indicate a failed ddcutil call the first N
        times, followed by successful responses.
        """

        def __init__(self, erroneous_attempts: int):
            self.remaining_erroneous_attempts = erroneous_attempts

        def call(self, *args, **kwargs) -> CommandOutput:
            if self.remaining_erroneous_attempts > 0:
                self.remaining_erroneous_attempts -= 1
                return erroneous_command_output
            else:
                return default_command_output

    custom_options = dict(DEFAULT_OPTIONS)
    custom_options['brute_force_attempts'] = 5
    ddcutil_wrapper = DdcutilWrapper(custom_options)

    erroneous_attempt_provider = ErroneousAttemptProvider(erroneous_attempts)
    with mock.patch('ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper',
                    side_effect=erroneous_attempt_provider.call) as mocked_fn:
        output = await ddcutil_wrapper.run_async(ddcutil_verbs, bus=0, logger=silent_logger)
    # 6 attempts equals first regular attempt followed by five more attempts.
    assert mocked_fn.call_count == min(erroneous_attempts + 1, 6)
    assert mocked_fn.call_args_list == [
        call(f'ddcutil {"--bus 0 " if ddcutil_verbs != "detect" else ""}{ddcutil_verbs}', silent_logger),
    ] * mocked_fn.call_count

    if erroneous_attempts < custom_options['brute_force_attempts'] + 1:
        assert output == default_command_output
    else:
        assert output == erroneous_command_output


# noinspection SpellCheckingInspection
async def test_strip_nvidia_warning(silent_logger, default_ddcutil_wrapper):
    regular_output = 'VCP 10 C 50 100\n'
    error_message = '(is_nvidia_einval_bug          ) nvida/i2c-dev bug encountered. Forcing future io I2C_IO_STRATEGY_FILEIO. Retrying\n'
    mocked_output = CommandOutput(stdout=regular_output + error_message, stderr='', return_code=0)
    with mock.patch('ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper',
                    return_value=mocked_output):
        assert await default_ddcutil_wrapper.run_async('getvcp', '10', bus=0, logger=silent_logger) \
               == CommandOutput(stdout=regular_output, stderr='', return_code=0)


def test_get_ddcutil_version(default_ddcutil_wrapper):
    sample_ddcutil_version_output = 'ddcutil 2.0.0-rc1\nBuilt with support for USB connected displays.\nBuilt without function failure simulation.\nBuilt with libdrm services.\n\nCopyright (C) 2015-2023 Sanford Rockowitz\nLicense GPLv2: GNU GPL version 2 or later <http://gnu.org/licenses/gpl.html>\nThis is free software: you are free to change and redistribute it.\nThere is NO WARRANTY, to the extent permitted by law.\n'
    with mock.patch('ddcci_plasmoid_backend.subprocess_wrappers.subprocess_wrapper',
                    return_value=CommandOutput(stdout=sample_ddcutil_version_output, stderr='', return_code=0)):
        assert default_ddcutil_wrapper.get_ddcutil_version() == '2.0.0-rc1'


def test_get_ddcutil_version_error(default_ddcutil_wrapper):
    with mock.patch('ddcci_plasmoid_backend.subprocess_wrappers.subprocess_wrapper',
                    side_effect=CalledProcessError(1, 'ddcutil --version')), \
            pytest.raises(OSError):
        default_ddcutil_wrapper.get_ddcutil_version()
