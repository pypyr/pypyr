"""Unit tests for subproc.py."""
import subprocess

import pytest

from pypyr.errors import ContextError
from pypyr.subproc import Command

# region Command


def test_subproc_command_eq():
    """Command instance does equality check on all members."""
    c = Command('cmd')
    assert c == c
    assert Command('cmd') == Command('cmd')
    assert Command('cmd') != Command('other')

    assert Command([1, 2, 3]) == Command([1, 2, 3])
    assert Command([1, 2, 3]) != Command([11, 22, 33])

    assert Command('arb') != 'arb'

    assert Command('cmd',
                   is_shell=True,
                   cwd='cwd',
                   is_save=False,
                   is_text=True,
                   stdout='out',
                   stderr='err',
                   encoding='enc',
                   append=True) == Command('cmd',
                                           is_shell=True,
                                           cwd='cwd',
                                           is_save=False,
                                           is_text=True,
                                           stdout='out',
                                           stderr='err',
                                           encoding='enc',
                                           append=True)

    assert Command('cmd',
                   is_shell=False,
                   cwd='cwd',
                   is_save=False,
                   is_text=True,
                   stdout='out',
                   stderr='err',
                   encoding='enc',
                   append=False) != Command('cmd',
                                            is_shell=False,
                                            cwd='cwd',
                                            is_save=False,
                                            is_text=True,
                                            stdout='out',
                                            stderr='err',
                                            encoding='enc',
                                            append=True)
    assert Command('cmd',
                   is_shell=True,
                   cwd='cwd',
                   is_save=False,
                   is_text=True,
                   stdout='out',
                   stderr='err',
                   encoding='enc1',
                   append=True) != Command('cmd',
                                           is_shell=True,
                                           cwd='cwd',
                                           is_save=False,
                                           is_text=True,
                                           stdout='out',
                                           stderr='err',
                                           encoding='enc2',
                                           append=True)
    assert Command('cmd',
                   is_shell=True,
                   cwd='cwd',
                   is_save=True,
                   is_text=True,
                   encoding='enc',
                   append=True) == Command('cmd',
                                           is_shell=True,
                                           cwd='cwd',
                                           is_save=True,
                                           is_text=True,
                                           encoding='enc',
                                           append=True)

    assert [Command('one')] == [Command('one')]
    assert [Command('one')] != [Command('two')]

    # results
    cmd1 = Command('cmd')
    cmd1.results.append('one')
    cmd2 = Command('cmd')
    cmd2.results.append('one')
    assert cmd1 == cmd2
    cmd2.results.append('two')
    assert cmd1 != cmd2


def test_subproc_command_no_stdout_on_save():
    """Raise when combining stdout/stdour with save."""
    #  stdin
    with pytest.raises(ContextError) as err:
        Command('arb', is_save=True, stdout='in')

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")

    #  stdout
    with pytest.raises(ContextError) as err:
        Command('arb', is_save=True, stderr='out')

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")

    #  stdin + stdout
    with pytest.raises(ContextError) as err:
        Command('arb', is_save=True, stdout='in', stderr='out')

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")


def test_subproc_command_output_handles_none():
    """Output handles return None."""
    cmd = Command('arb')
    with cmd.output_handles() as (stdout, stderr):
        assert stdout is None
        assert stderr is None


def test_subproc_command_output_handles_dev_null():
    """Output handles to /dev/null."""
    cmd = Command('arb', stdout='/dev/null', stderr='/dev/null')
    with cmd.output_handles() as (stdout, stderr):
        assert stdout == subprocess.DEVNULL
        assert stderr == subprocess.DEVNULL

    cmd = Command('arb', stderr='/dev/null')
    with cmd.output_handles() as (stdout, stderr):
        assert stdout is None
        assert stderr == subprocess.DEVNULL

    cmd = Command('arb', stdout='/dev/null')
    with cmd.output_handles() as (stdout, stderr):
        assert stdout == subprocess.DEVNULL
        assert stderr is None

    cmd = Command('arb', stdout='/dev/null', stderr='/dev/stdout')
    with cmd.output_handles() as (stdout, stderr):
        assert stdout == subprocess.DEVNULL
        assert stderr == subprocess.STDOUT
# endregion Command
