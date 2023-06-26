import logging
import subprocess
from subprocess import CalledProcessError

import pytest

from ddcci_plasmoid_backend import subprocess


@pytest.fixture
def silent_logger():
    logger = logging.getLogger('test_subprocess_wrapper')
    # silence it
    logger.setLevel(logging.CRITICAL + 1)
    return logger


@pytest.fixture
def stdout_stderr_test():
    # File descriptor 1 is stdout, 2 is stderr
    return ['python', '-c', 'import os; os.write(1, b"test-stdout"); os.write(2, b"test-stderr")']


def test_subprocess_wrapper_success(silent_logger, stdout_stderr_test):
    output = subprocess.subprocess_wrapper(*stdout_stderr_test, logger=silent_logger)
    assert output.stdout == 'test-stdout'
    assert output.stderr == 'test-stderr'
    assert output.returnCode == 0


def test_subprocess_wrapper_fail(silent_logger):
    # /usr/bin/false will always return a return code of 1
    with pytest.raises(CalledProcessError):
        subprocess.subprocess_wrapper('false', logger=silent_logger)


def test_subprocess_wrapper_logger_none():
    subprocess.subprocess_wrapper('true')


async def test_async_subprocess_wrapper_success(silent_logger, stdout_stderr_test):
    output = await subprocess.async_subprocess_wrapper(*stdout_stderr_test, logger=silent_logger)
    assert output.stdout == 'test-stdout'
    assert output.stderr == 'test-stderr'
    assert output.returnCode == 0


async def test_async_subprocess_wrapper_fail(silent_logger):
    # /usr/bin/false will always return a return code of 1
    with pytest.raises(CalledProcessError):
        await subprocess.async_subprocess_wrapper('false', logger=silent_logger)


def test_async_subprocess_wrapper_logger_none():
    subprocess.subprocess_wrapper('true')
