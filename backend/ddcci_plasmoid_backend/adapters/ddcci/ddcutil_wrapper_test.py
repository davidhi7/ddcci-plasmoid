from __future__ import annotations

from unittest import mock
from unittest.mock import MagicMock, call

import pytest
from pytest_asyncio import fixture

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.adapters.ddcci.ddcutil_wrapper import DdcutilWrapper
from ddcci_plasmoid_backend.subprocess_wrappers import CalledProcessError, CommandOutput


@fixture(scope="function")
def mock_subprocess_wrapper(default_command_output):
    with mock.patch(
        "ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper",
        return_value=default_command_output,
    ) as mocked_function:
        yield mocked_function


@fixture(params=["detect", "capabilities", "getvcp", "setvcp"])
def ddcutil_verbs(request):
    return request.param


async def test_basic_functionality(
    silent_logger,
    default_ddcutil_wrapper,
    ddcutil_verbs,
    mock_subprocess_wrapper: MagicMock,
    default_command_output,
):
    assert (
        await default_ddcutil_wrapper.run_async(
            ddcutil_verbs, "arg1", "arg2", bus=0, logger=silent_logger
        )
        == default_command_output
    )
    mock_subprocess_wrapper.assert_called_once_with(
        f'ddcutil {"--bus 0 " if ddcutil_verbs != "detect" else ""}{ddcutil_verbs} arg1'
        " arg2",
        silent_logger,
    )


@pytest.mark.usefixtures("mock_subprocess_wrapper")
async def test_detect_bus_error(
    silent_logger,
    default_ddcutil_wrapper,
    ddcutil_verbs,
):
    if ddcutil_verbs != "detect":
        with pytest.raises(ValueError):
            await default_ddcutil_wrapper.run_async(ddcutil_verbs, logger=silent_logger)


async def test_sleep_multiplier(
    silent_logger, ddcutil_verbs, mock_subprocess_wrapper: MagicMock
):
    custom_config = config.init(None)["ddcci"]
    custom_config["ddcutil_sleep_multiplier"] = "1.5"
    ddcutil_wrapper = DdcutilWrapper(custom_config)
    await ddcutil_wrapper.run_async(ddcutil_verbs, "arg1", bus=0, logger=silent_logger)
    mock_subprocess_wrapper.assert_called_once_with(
        f'ddcutil {"--bus 0 " if ddcutil_verbs != "detect" else ""}'
        f"--sleep-multiplier 1.5 {ddcutil_verbs} arg1",
        silent_logger,
    )


async def test_no_verify(silent_logger, mock_subprocess_wrapper: MagicMock):
    custom_config = config.init(None)["ddcci"]
    custom_config["ddcutil_no_verify"] = "True"
    ddcutil_wrapper = DdcutilWrapper(custom_config)
    await ddcutil_wrapper.run_async("setvcp", "arg1", bus=0, logger=silent_logger)
    mock_subprocess_wrapper.assert_called_once_with(
        "ddcutil --bus 0 setvcp --noverify arg1", silent_logger
    )


@pytest.mark.parametrize("erroneous_attempts", [6, 3])
async def test_brute_force_attempts(
    silent_logger, ddcutil_verbs, default_command_output, erroneous_attempts
):
    erroneous_command_output = CommandOutput(
        stdout="DDC communication failed", stderr="", return_code=0
    )

    class ErroneousAttemptProvider:
        """
        Implement a solution that provides CommandOutput instances that indicate a failed ddcutil
        call the first N times, followed by successful responses.
        """

        def __init__(self, erroneous_attempts: int):
            self.remaining_erroneous_attempts = erroneous_attempts

        # noinspection PyUnusedLocal
        def call(self, *args, **kwargs) -> CommandOutput:
            if self.remaining_erroneous_attempts > 0:
                self.remaining_erroneous_attempts -= 1
                return erroneous_command_output
            return default_command_output

    custom_config = config.init(None)["ddcci"]
    custom_config["brute_force_attempts"] = "5"
    ddcutil_wrapper = DdcutilWrapper(custom_config)

    erroneous_attempt_provider = ErroneousAttemptProvider(erroneous_attempts)
    with mock.patch(
        "ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper",
        side_effect=erroneous_attempt_provider.call,
    ) as mocked_fn:
        output = await ddcutil_wrapper.run_async(
            ddcutil_verbs, bus=0, logger=silent_logger
        )
    # 6 attempts equals first regular attempt followed by five more attempts.
    assert mocked_fn.call_count == min(erroneous_attempts + 1, 6)
    assert (
        mocked_fn.call_args_list
        == [
            call(
                "ddcutil"
                f" {'--bus 0 ' if ddcutil_verbs != 'detect' else ''}{ddcutil_verbs}",
                silent_logger,
            ),
        ]
        * mocked_fn.call_count
    )

    if erroneous_attempts < custom_config.getint("brute_force_attempts") + 1:
        assert output == default_command_output
    else:
        assert output == erroneous_command_output


@pytest.mark.parametrize(
    "error_message",
    [
        (
            "(is_nvidia_einval_bug          ) nvida/i2c-dev bug encountered. Forcing future"
            " io I2C_IO_STRATEGY_FILEIO. Retrying\n"
        ),
        (
            "Unable to open directory /sys/bus/i2c/devices/i2c--1: No such file or directory\n"
            "Device /dev/i2c-255 does not exist. Error = ENOENT(2): No such file or directory\n"
            "/sys/bus/i2c buses without /dev/i2c-N devices: /sys/bus/i2c/devices/i2c-255\n"
            "Driver i2c_dev must be loaded or builtin\n"
            "See https://www.ddcutil.com/kernel_module\n"
        ),
        (
            "busno=6, Feature 0xdd should not exist but ddc_get_nontable_vcp_value() succeeds, "
            "returning mh=0x00 ml=0x64 sh=0x00 sl=0x64\n"
        ),
    ],
)
# noinspection SpellCheckingInspection
async def test_strip_ddcutil_warnings(
    silent_logger, default_ddcutil_wrapper, error_message
):
    regular_output = "VCP 10 C 50 100\n"
    mocked_output = CommandOutput(
        stdout=error_message + regular_output, stderr="", return_code=0
    )
    with mock.patch(
        "ddcci_plasmoid_backend.subprocess_wrappers.async_subprocess_wrapper",
        return_value=mocked_output,
    ):
        assert await default_ddcutil_wrapper.run_async(
            "getvcp", "10", bus=0, logger=silent_logger
        ) == CommandOutput(stdout=regular_output, stderr="", return_code=0)


def test_get_ddcutil_version(default_ddcutil_wrapper):
    sample_ddcutil_version_output = (
        "ddcutil 2.0.0-rc1\nBuilt with support for USB connected displays.\nBuilt"
        " without function failure simulation.\nBuilt with libdrm"
        " services.\n\nCopyright (C) 2015-2023 Sanford Rockowitz\nLicense GPLv2: GNU"
        " GPL version 2 or later <http://gnu.org/licenses/gpl.html>\nThis is free"
        " software: you are free to change and redistribute it.\nThere is NO WARRANTY,"
        " to the extent permitted by law.\n"
    )
    with mock.patch(
        "ddcci_plasmoid_backend.subprocess_wrappers.subprocess_wrapper",
        return_value=CommandOutput(
            stdout=sample_ddcutil_version_output, stderr="", return_code=0
        ),
    ):
        assert default_ddcutil_wrapper.get_ddcutil_version() == "2.0.0-rc1"


def test_get_ddcutil_version_error(default_ddcutil_wrapper):
    with mock.patch(
        "ddcci_plasmoid_backend.subprocess_wrappers.subprocess_wrapper",
        side_effect=CalledProcessError(1, "ddcutil --version"),
    ), pytest.raises(OSError):
        default_ddcutil_wrapper.get_ddcutil_version()
