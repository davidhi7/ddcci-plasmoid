from __future__ import annotations

import asyncio
import re
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import logging


@dataclass
class CommandOutput:
    return_code: int
    stdout: str
    stderr: str


class CalledProcessError(subprocess.CalledProcessError):
    pass


def subprocess_wrapper(command: str, logger: logging.Logger) -> CommandOutput:
    """
    Wrapper for synchronous subprocess calls to simplify logging and testing

    Args:
        command: String command to execute
        logger: Logger that is used for logging outputs.

    Returns:
        Data of the finished subprocess
    """
    logger.info(f"Execute command: `{command}`")
    proc = subprocess.run(command, capture_output=True, shell=True)
    stdout = proc.stdout.decode()
    stderr = proc.stderr.decode()
    command_output = CommandOutput(proc.returncode, stdout, stderr)

    if logger:
        _log_subprocess_output(command, command_output, logger)
    if proc.returncode > 0:
        raise CalledProcessError(
            returncode=proc.returncode, cmd=command, output=stdout, stderr=stderr
        )
    return command_output


async def async_subprocess_wrapper(
    command: str, logger: logging.Logger
) -> CommandOutput:
    """
    Wrapper for asynchronous subprocess calls to simplify logging and testing

    Args:
        command: String command to execute
        logger: Logger that is used for logging outputs.

    Returns:
        Data of the finished subprocess
    """
    logger.info(f"Execute command: `{command}`")
    proc = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    await proc.wait()
    # it's safe to assume that the return code is not None at this point
    return_code: int = 1 if proc.returncode is None else proc.returncode
    stdout, stderr = await proc.communicate()
    stdout = stdout.decode()
    stderr = stderr.decode()
    command_output = CommandOutput(return_code, stdout, stderr)

    if logger:
        _log_subprocess_output(command, command_output, logger)
    if return_code > 0:
        raise CalledProcessError(
            returncode=return_code, cmd=command, output=stdout, stderr=stderr
        )
    return command_output


def _log_subprocess_output(
    cmd: str, output: CommandOutput, logger: logging.Logger
) -> None:
    # remove trailing newlines for better readability
    stripped_stdout = re.sub(r"\n$", "", output.stdout)
    stripped_stderr = re.sub(r"\n$", "", output.stderr)
    logger.debug(f"[code]   {cmd}: {output.return_code}")
    logger.debug(f"[stdout] {cmd}: {stripped_stdout}")
    logger.debug(f"[stderr] {cmd}: {stripped_stderr}\n")
