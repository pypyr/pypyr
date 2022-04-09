"""Tests for pypyr.steps.cmd that touch the filesystem.

Can't use pyfakefs for these because the subprocess lib uses C libs to hit the
fs rather than the patch-able Python files access.
"""
from pathlib import Path
import subprocess
import tempfile

import pytest

from pypyr.config import config
from pypyr.context import Context
import pypyr.steps.cmd

is_windows = config.is_windows


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    return win if is_windows else posix


@pytest.fixture
def temp_dir():
    """Make tmp dir in testfiles/out. Yields pathlib.Path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_cmd_run_has_list_input_output_to_file(temp_dir):
    """List input to run complex dict save all output to files."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two three',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    stdout = temp_dir.joinpath('cmdout/stdout')
    stderr = temp_dir.joinpath('cmdout2/stderr')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2],
            'stdout': stdout,
            'stderr': stderr}
    })
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context

    assert stdout.read_text() == 'one\ntwo three\n'
    assert stderr.read_text() == ''


def test_cmd_run_has_list_input_error_throws_and_stderr(temp_dir):
    """Write to stdout and stderr."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                   r'tests\testfiles\cmds\exitwitherr.bat')

    # won't run, because 2 errors. test assert checks it doesn't run.
    cmd3 = get_cmd('echo three',
                   r'tests\testfiles\cmds\echo.bat three')

    stdout = temp_dir.joinpath('stdout')
    stderr = temp_dir.joinpath('stderr')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2, cmd3],
            'stdout': stdout,
            'stderr': stderr}
    })

    with pytest.raises(subprocess.CalledProcessError):
        pypyr.steps.cmd.run_step(context)

    assert stdout.read_text() == 'one\n'
    assert stderr.read_text() == 'arb err here\n'


def test_cmd_run_has_list_input_error_stderr_to_stdout(temp_dir):
    """Redirect stderr to stdout."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                   r'tests\testfiles\cmds\exitwitherr.bat')

    # won't run, because 2 errors. test assert checks it doesn't run.
    cmd3 = get_cmd('echo three',
                   r'tests\testfiles\cmds\echo.bat three')

    stdout = temp_dir.joinpath('stdout')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2, cmd3],
            'stdout': stdout,
            'stderr': '/dev/stdout'}
    })

    with pytest.raises(subprocess.CalledProcessError):
        pypyr.steps.cmd.run_step(context)

    assert stdout.read_text() == 'one\narb err here\n'


def test_cmd_run_has_list_input_overwrite_vs_append(temp_dir):
    """Write to stdout and stderr with append true/false, default overwrite."""
    stdout = temp_dir.joinpath('stdout')
    stderr = temp_dir.joinpath('stderr')

    cmd1 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh one',
                   r'tests\testfiles\cmds\echo-out-and-err.bat one')

    cmd2 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh two',
                   r'tests\testfiles\cmds\echo-out-and-err.bat two')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2],
            'stdout': stdout,
            'stderr': stderr}
    })

    pypyr.steps.cmd.run_step(context)

    assert stdout.read_text() == 'stdout one\nstdout two\n'
    assert stderr.read_text() == 'stderr one\nstderr two\n'

    # now overwrite these by default on 2nd invocation
    cmd3 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh three',
                   r'tests\testfiles\cmds\echo-out-and-err.bat three')

    cmd4 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh four',
                   r'tests\testfiles\cmds\echo-out-and-err.bat four')

    context = Context({
        'cmd': {
            'run': [cmd3, cmd4],
            'stdout': stdout,
            'stderr': stderr}
    })

    pypyr.steps.cmd.run_step(context)

    assert stdout.read_text() == 'stdout three\nstdout four\n'
    assert stderr.read_text() == 'stderr three\nstderr four\n'

    # now append
    cmd5 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh five',
                   r'tests\testfiles\cmds\echo-out-and-err.bat five')

    cmd6 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh six',
                   r'tests\testfiles\cmds\echo-out-and-err.bat six')

    context = Context({
        'cmd': {
            'run': [cmd5, cmd6],
            'stdout': stdout,
            'stderr': stderr,
            'append': True}
    })

    pypyr.steps.cmd.run_step(context)

    assert stdout.read_text() == (
        'stdout three\nstdout four\nstdout five\nstdout six\n')
    assert stderr.read_text() == (
        'stderr three\nstderr four\nstderr five\nstderr six\n')
