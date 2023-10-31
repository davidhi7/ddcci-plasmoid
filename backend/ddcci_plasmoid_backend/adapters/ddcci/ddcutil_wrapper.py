from __future__ import annotations

import dataclasses
import logging
import re
from typing import TYPE_CHECKING

from ddcci_plasmoid_backend import subprocess_wrappers
from ddcci_plasmoid_backend.errors import DdcutilError
from ddcci_plasmoid_backend.subprocess_wrappers import CalledProcessError

if TYPE_CHECKING:
    from configparser import SectionProxy

    pass

logger = logging.getLogger(__name__)
ddcutil_failure_pattern = re.compile("(DDC communication failed)")
DDCUTIL_DEFAULT_SLEEP_MULTIPLIER = 1.0


class DdcutilWrapper:
    def __init__(self, config_section: SectionProxy) -> None:
        self.ddcutil_executable = config_section.get("ddcutil_executable")
        self.sleep_multiplier = config_section.getfloat("ddcutil_sleep_multiplier")
        self.no_verify = config_section.getboolean("ddcutil_no_verify")
        self.brute_force_attempts = config_section.getint("brute_force_attempts")

    async def run_async(
        self, verb: str, *arguments: str, bus: int | None = None, logger: logging.Logger
    ) -> subprocess_wrappers.CommandOutput:
        """
        Run a ddcutil command asynchronously.

        Args:
            verb: ddcutil verb (e.g. detect, getvcp)
            *arguments: Additional arguments to pass to ddcutil
            bus: i2c bus number
            logger: Logger used for debug output

        Returns:
            CommandOutput
        """
        command = self._build_command(verb, *arguments, bus=bus)
        try:
            output = await subprocess_wrappers.async_subprocess_wrapper(command, logger)
            attempt = 0
            while re.findall(ddcutil_failure_pattern, output.stdout):
                if attempt == self.brute_force_attempts:
                    # Do not show info message if failure pattern was found on first and only attempt
                    if attempt > 0:
                        logger.warning(
                            f"Command `{command}` failed {attempt + 1} times in a row"
                        )
                    break
                attempt += 1
                output = await subprocess_wrappers.async_subprocess_wrapper(
                    command, logger
                )
            else:
                # while ... else is only executed if the queue has not been exited with break but with
                # a false loop condition
                if attempt > 0:
                    logger.info(f"Required {attempt} attempts for command `{command}`")
            return self._strip_irrelevant_error_messages(output)
        except CalledProcessError as exc:
            msg = f"Running ddcutil command `{command}` failed"
            raise DdcutilError(msg) from exc

    def _build_command(self, verb: str, *arguments: str, bus: int | None) -> str:
        command = [self.ddcutil_executable]
        if bus is not None:
            if verb == "detect":
                logger.warning("Explicit i2c bus unsupported for `detect` verb")
            else:
                command.append("--bus")
                command.append(str(bus))
        elif verb != "detect":
            msg = f"i2c bus missing for `{verb}` verb"
            raise ValueError(msg)
        if (
            self.sleep_multiplier
            and self.sleep_multiplier != DDCUTIL_DEFAULT_SLEEP_MULTIPLIER
        ):
            command.append("--sleep-multiplier")
            command.append(str(self.sleep_multiplier))
        command.append(verb)
        if verb == "setvcp" and self.no_verify is True:
            command.append("--noverify")
        elif self.no_verify is True:
            logger.warning("`--noverify` is not supported for verbs but `setvcp`")
        command.extend(arguments)
        return " ".join(command)

    @staticmethod
    def _strip_irrelevant_error_messages(
        command_output: subprocess_wrappers.CommandOutput,
    ) -> subprocess_wrappers.CommandOutput:
        """Return a new CommandOutput instance with multiple ddcutil warnings/errors in stdout
        output removed. Fix for #32 and multiple other bugs.

        Args:
            command_output: CommandOutput to work with

        Returns:
            New CommandOutput instance with warning messages removed
        """
        error_messages = [
            # #32, `nvida`: typo is in ddcutil source
            (
                "(is_nvidia_einval_bug          ) nvida/i2c-dev bug encountered. Forcing"
                " future io I2C_IO_STRATEGY_FILEIO. Retrying\n"
            ),
            # Common error with ddcutil versions prior to 1.4.1
            "Unable to open directory /sys/bus/i2c/devices/i2c--1: No such file or directory\n",
            "Device /dev/i2c-255 does not exist. Error = ENOENT(2): No such file or directory\n",
            "/sys/bus/i2c buses without /dev/i2c-N devices: /sys/bus/i2c/devices/i2c-255\n",
            "Driver i2c_dev must be loaded or builtin\n",
            "See https://www.ddcutil.com/kernel_module\n",
        ]
        fixed_stdout = command_output.stdout
        for entry in error_messages:
            fixed_stdout = fixed_stdout.replace(entry, "")

        return dataclasses.replace(command_output, stdout=fixed_stdout)

    def get_ddcutil_version(self) -> str:
        """
        Get the ddcutil version string.
        Returns:
             ddcutil version string, e.g. 2.0.0-rc1
        """
        try:
            silent_logger = logging.getLogger("silent")
            silent_logger.setLevel(logging.CRITICAL + 1)
            output = subprocess_wrappers.subprocess_wrapper(
                f"{self.ddcutil_executable} --version", logger=silent_logger
            )
            # First line of ddcutil output contains the version with a value like
            # 'ddcutil 2.0.0-rc1'.Then remove 'ddcutil' and the trailing whitespace
            return output.stdout.split("\n")[0].replace("ddcutil", "").strip()
        except CalledProcessError as error:
            msg = "Failed to invoke ddcutil"
            raise DdcutilError(msg) from error
