import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass


@dataclass
class CommandOutput:
    return_code: int
    stdout: str
    stderr: str


def subprocess_wrapper(program: str, *args: str, logger: logging.Logger = None) -> CommandOutput:
    """
    Wrapper for synchronous subprocess calls to simplify logging and testing

    Args:
        program: Executable
        *args: list of arguments
        logger: Logger that is used for logging outputs. If None, nothing is logged.

    Returns:
        Data of the finished subprocess
    """
    command_string = " ".join([program, *args])
    if logger:
        logger.debug(f'Execute command: `{command_string}`')
    proc = subprocess.run([program, *args], capture_output=True)
    stdout = proc.stdout.decode()
    stderr = proc.stderr.decode()
    command_output = CommandOutput(proc.returncode, stdout, stderr)

    if logger:
        _log_subprocess_output(' '.join(command_string), command_output, logger)
    if proc.returncode > 0:
        raise subprocess.CalledProcessError(returncode=proc.returncode, cmd=[program, *args], output=stdout,
                                            stderr=stderr)
    return command_output


async def async_subprocess_wrapper(program: str, *args: str, logger: logging.Logger = None) -> CommandOutput:
    """
    Wrapper for asynchronous subprocess calls to simplify logging and testing

    Args:
        program: Executable
        *args: list of arguments
        logger: Logger that is used for logging outputs. If None, nothing is logged.

    Returns:
        Data of the finished subprocess
    """
    command_string = " ".join([program, *args])
    if logger:
        logger.debug(f'Execute command: `{command_string}`')
    proc = await asyncio.subprocess.create_subprocess_exec(program, *args,
                                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await proc.wait()
    # it's safe to assume that the return code is not None at this point
    return_code: int = 1 if proc.returncode is None else proc.returncode
    stdout, stderr = await proc.communicate()
    stdout = stdout.decode()
    stderr = stderr.decode()
    command_output = CommandOutput(return_code, stdout, stderr)

    if logger:
        _log_subprocess_output(command_string, command_output, logger)
    if return_code > 0:
        raise subprocess.CalledProcessError(returncode=return_code, cmd=[program, *args], output=stdout, stderr=stderr)
    return command_output


def _log_subprocess_output(cmd: str, output: CommandOutput, logger: logging.Logger):
    # remove trailing newlines for better readability
    stripped_stdout = re.sub(r"\n$", "", output.stdout)
    stripped_stderr = re.sub(r"\n$", "", output.stderr)
    logger.debug(f'[code]   {cmd}: {output.return_code}')
    logger.debug(f'[stdout] {cmd}: {stripped_stdout}')
    logger.debug(f'[stderr] {cmd}: {stripped_stderr}\n')
