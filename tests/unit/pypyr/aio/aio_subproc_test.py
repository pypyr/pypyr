"""Unit tests for pypyr.aio.subproc."""
import asyncio.subprocess as subprocess
import locale

import pytest

from pypyr.errors import ContextError
from pypyr.aio.subproc import Command, Commands

# region Command

# region ctor


def test_async_subproc_minimal():
    """Create Command with minimal inputs."""
    cmd = Command('arb')
    assert cmd.cmd == 'arb'
    assert cmd.is_shell is False
    assert cmd.cwd is None
    assert cmd.is_save is False
    assert cmd.is_text is False
    assert cmd.stdout is None
    assert cmd.stderr is None
    assert cmd.encoding == locale.getpreferredencoding(False)
    assert cmd.append is False
    assert cmd.results == []


def test_async_subproc_maximal():
    """Create Command with maximal inputs."""
    # is_save
    cmd = Command('arb',
                  is_shell=True,
                  cwd='cwd',
                  is_save=True,
                  is_text=True,
                  encoding='enc',
                  append=True)

    assert cmd.cmd == 'arb'
    assert cmd.is_shell is True
    assert cmd.cwd == 'cwd'
    assert cmd.is_save is True
    assert cmd.is_text is True
    assert cmd.stdout == subprocess.PIPE
    assert cmd.stderr == subprocess.PIPE
    assert cmd.encoding == 'enc'
    assert cmd.append is True
    assert cmd.results == []

    # not is_save
    cmd = Command('arb',
                  is_shell=True,
                  cwd='cwd',
                  is_save=False,
                  is_text=True,
                  stdout='stdout',
                  stderr='stderr',
                  encoding='enc',
                  append=True)

    assert cmd.cmd == 'arb'
    assert cmd.is_shell is True
    assert cmd.cwd == 'cwd'
    assert cmd.is_save is False
    assert cmd.is_text is False  # because save is False
    assert cmd.stdout == 'stdout'
    assert cmd.stderr == 'stderr'
    assert cmd.encoding == 'enc'
    assert cmd.append is True
    assert cmd.results == []


def test_async_subproc_command_no_stdout_on_save():
    """Raise when combining stdout/stdour with save."""
    #  stdout
    with pytest.raises(ContextError) as err:
        Command('arb', is_save=True, stdout='in')

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")

    #  stderr
    with pytest.raises(ContextError) as err:
        Command('arb', is_save=True, stderr='out')

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")

    #  stderr + stdout
    with pytest.raises(ContextError) as err:
        Command('arb', is_save=True, stdout='in', stderr='out')

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")
# endregion ctor


def test_async_subproc_command_eq():
    """Command instance does equality check on all attributes."""
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

# region parse_results


def test_async_subproc_command_parse_result_wrong_type():
    """Results should only contain Exception, SubprocessResult or list."""
    cmd = Command("arb")
    # this is pretty artificial - this err is there as a safety mechanism in
    # case of unforeseen future changes where maybe someone (me?!) forgets
    # results should only contain Exception, SubprocessResult or list.
    cmd.results.append(123)
    with pytest.raises(TypeError) as err:
        cmd.parse_results()

    # noqa is for line length
    assert str(err.value) == """\
123 is <class 'int'>.
It should be SubprocessResult | Exception | list[SubprocessResult | Exception]."""  # noqa: E501
# endregion parse_results

# region output_handles


def test_async_subproc_command_output_handles_none():
    """Output handles return None."""
    cmd = Command('arb')
    with cmd.output_handles() as (stdout, stderr):
        assert stdout is None
        assert stderr is None


def test_async_subproc_command_output_handles_pipe():
    """Output handles to pipe (capture)."""
    cmd = Command('arb', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with cmd.output_handles() as (stdout, stderr):
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE


def test_async_subproc_command_output_handles_dev_null():
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
# endregion output_handles

# endregion Command

# region Commands


def test_async_subproc_commands_iter():
    """Commands is iterable and index-able."""
    cmds = Commands()
    assert len(cmds) == 0

    for c in cmds:
        raise AssertionError("can't iterate empty")

    cmds.append(Command('a'))
    cmds.append(Command('b'))

    assert len(cmds) == 2

    out = []
    for c in cmds:
        out.append(c)

    assert out == [Command('a'), Command('b')]

    assert cmds[0] == Command('a')
    assert cmds[1] == Command('b')
    assert cmds[1] != Command('c')


def test_async_subproc_commands_eq():
    """Command instance does equality check on all attributes."""
    c = Commands()
    assert c == c

    empty_cmds = Commands()
    assert empty_cmds == Commands()

    cmds = Commands()
    cmds.append(Command('a'))

    assert cmds != empty_cmds

    cmds2 = Commands()
    cmds2.append(Command('a'))

    assert cmds == cmds2
    cmds2.append(Command('b'))
    assert cmds != cmds2
    cmds.append(Command('b'))
    assert cmds == cmds2

    assert cmds != 123

# endregion Commands
