import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass


@dataclass
class CommandOutput:
    returnCode: int
    stdout: str
    stderr: str


# Wrap sync and async subprocess calls for mocking
def subprocess_wrapper(cmd: list[str] | str, *, logger: logging.Logger) -> CommandOutput:
    if isinstance(cmd, str):
        cmd = cmd.split(' ')
    logger.debug(f'Execute command: `{" ".join(cmd)}`')
    proc = subprocess.run(cmd, capture_output=True)
    stdout = proc.stdout.decode()
    stderr = proc.stderr.decode()
    command_output = CommandOutput(proc.returncode, stdout, stderr)

    _log_subprocess_output(' '.join(cmd), command_output, logger)
    if proc.returncode > 0:
        raise subprocess.CalledProcessError(returncode=proc.returncode, cmd=cmd, output=stdout, stderr=stderr)
    return command_output


async def async_subprocess_wrapper(program: str, *args: str, logger: logging.Logger) -> CommandOutput:
    command_string = " ".join((program,) + args)
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

    _log_subprocess_output(command_string, command_output, logger)
    if return_code > 0:
        raise subprocess.CalledProcessError(returncode=return_code, cmd=command_string, output=stdout, stderr=stderr)
    return command_output


def _log_subprocess_output(cmd: str, output: CommandOutput, logger: logging.Logger):
    # remove trailing newlines for better readability
    stripped_stdout = re.sub(r"\n$", "", output.stdout)
    stripped_stderr = re.sub(r"\n$", "", output.stderr)
    logger.debug(f'[code]   {cmd}: {output.returnCode}')
    logger.debug(f'[stdout] {cmd}: {stripped_stdout}')
    logger.debug(f'[stderr] {cmd}: {stripped_stderr}\n')
