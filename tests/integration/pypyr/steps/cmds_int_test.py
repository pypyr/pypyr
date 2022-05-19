"""Tests for pypyr.steps.cmds that touch the filesystem.

Can't use pyfakefs for these because the subprocess lib uses C libs to hit the
fs rather than the patch-able Python files access.
"""
from pathlib import Path
import tempfile
from unittest import TestCase

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import MultiError, SubprocessError
import pypyr.steps.cmds

is_windows = config.is_windows


@pytest.fixture
def temp_dir():
    """Make tmp dir in testfiles/out. Yields pathlib.Path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    return win if is_windows else posix


def test_async_cmds_stderr_to_stdout(temp_dir):
    """Redirect stderr to stdout."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                   r'tests\testfiles\cmds\exitwitherr.bat')

    cmd3 = get_cmd('echo three',
                   r'tests\testfiles\cmds\echo.bat three')

    stdout = temp_dir.joinpath('stdout')

    context = Context({
        'cmds': {
            'run': [cmd1, cmd2, cmd3],
            'stdout': stdout,
            'stderr': '/dev/stdout'}
    })

    with pytest.raises(MultiError) as ex:
        pypyr.steps.cmds.run_step(context)

    assert 'cmdOut' not in context
    err = ex.value
    assert len(err) == 1
    the_err = err[0]
    assert type(the_err) is SubprocessError
    assert the_err.cmd == [cmd2]
    assert the_err.returncode == 1
    # None because save is False
    assert the_err.stderr is None

    out_file_lines = stdout.read_text().rstrip().split('\n')
    TestCase().assertCountEqual(out_file_lines,
                                ['one', 'arb err here', 'three'])


def test_async_cmds_overwrite_vs_append(temp_dir):
    """Write to stdout and stderr with append true/false, default overwrite."""
    stdout = temp_dir.joinpath('mydir/stdout')
    stderr = temp_dir.joinpath('mydir/stderr')

    cmd1 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh one',
                   r'tests\testfiles\cmds\echo-out-and-err.bat one')

    context = Context({
        'cmds': {
            'run': [cmd1],
            'stdout': stdout,
            'stderr': stderr}
    })

    pypyr.steps.cmds.run_step(context)

    assert 'cmdOut' not in context
    assert stdout.read_text() == 'stdout one\n'
    assert stderr.read_text() == 'stderr one\n'

    # now overwrite these by default on 2nd invocation
    cmd2 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh two',
                   r'tests\testfiles\cmds\echo-out-and-err.bat two')

    context = Context({
        'cmds': {
            'run': [cmd2],
            'stdout': stdout,
            'stderr': stderr}
    })

    pypyr.steps.cmds.run_step(context)

    assert stdout.read_text() == 'stdout two\n'
    assert stderr.read_text() == 'stderr two\n'

    # now append
    cmd3 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh three',
                   r'tests\testfiles\cmds\echo-out-and-err.bat three')

    # list input with element being a dict in expanded syntax
    context = Context({
        'cmds': [{
            'run': [cmd3],
            'stdout': stdout,
            'stderr': stderr,
            'append': True}]
    })

    pypyr.steps.cmds.run_step(context)

    assert 'cmdOut' not in context
    assert stdout.read_text() == (
        'stdout two\nstdout three\n')
    assert stderr.read_text() == (
        'stderr two\nstderr three\n')


def test_async_cmds_expanded_syntax_on_list_item(temp_dir):
    """Set stdout/stderr on multiple expanded inputs on base list input."""
    cmd1 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh one',
                   r'tests\testfiles\cmds\echo-out-and-err.bat one')

    cmd2 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh two',
                   r'tests\testfiles\cmds\echo-out-and-err.bat two')

    cmd3 = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh three',
                   r'tests\testfiles\cmds\echo-out-and-err.bat three')

    stdout1 = temp_dir.joinpath('stdout1')
    stderr1 = temp_dir.joinpath('stderr1')
    stdout2 = temp_dir.joinpath('stdout2')
    stderr2 = temp_dir.joinpath('stderr2')

    context = Context({
        'cmds': [
            {
                'run': [cmd1],
                'stdout': stdout1,
                'stderr': stderr1
            },
            {
                'run': [cmd2, cmd3],
                'stdout': stdout2,
                'stderr': stderr2}
        ]})

    pypyr.steps.cmds.run_step(context)

    assert 'cmdOut' not in context

    assert stdout1.read_text() == 'stdout one\n'
    assert stderr1.read_text() == 'stderr one\n'

    out_file_lines2 = stdout2.read_text().rstrip().split('\n')
    err_file_lines2 = stderr2.read_text().rstrip().split('\n')

    TestCase().assertCountEqual(out_file_lines2,
                                ['stdout two', 'stdout three'])

    TestCase().assertCountEqual(err_file_lines2,
                                ['stderr two', 'stderr three'])
