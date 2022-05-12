"""Unit tests for subproc.py."""
import subprocess

import pytest

from pypyr.context import Context
from pypyr.dsl import PyString
from pypyr.errors import ContextError, SubprocessError
from pypyr.subproc import Command, SubprocessResult

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

    #  stdout + stdout
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

# region SubprocessResult


def test_subprocessresult_check_returncode_zero():
    """Return None when returncode is 0."""
    sr = SubprocessResult('mycmd', 0, stdout='out', stderr='err')
    assert sr.check_returncode() is None


def test_subprocessresult_check_returncode_nonzero():
    """Return SubprocessError when returncode is non-zero."""
    sr = SubprocessResult('mycmd', 1, stdout='out', stderr='err')
    err = sr.check_returncode()
    assert type(err) is SubprocessError
    assert err.cmd == 'mycmd'
    assert err.returncode == 1
    assert err.stdout == 'out'
    assert err.stderr == 'err'

    sr = SubprocessResult('mycmd', -1, stdout='out', stderr='err')
    err = sr.check_returncode()
    assert type(err) is SubprocessError
    assert err.cmd == 'mycmd'
    assert err.returncode == -1
    assert err.stdout == 'out'
    assert err.stderr == 'err'

    sr = SubprocessResult('mycmd', 2)
    err = sr.check_returncode()
    assert type(err) is SubprocessError
    assert err.cmd == 'mycmd'
    assert err.returncode == 2
    assert err.stdout is None
    assert err.stderr is None


def test_subprocessresult_dict():
    """Get items like dict from SubprocessResult. For backwards compat."""
    sr = SubprocessResult('mycmd', 123, stdout='out', stderr='err')
    assert sr['cmd'] == 'mycmd'
    assert sr['returncode'] == 123
    assert sr['stdout'] == 'out'
    assert sr['stderr'] == 'err'

    # works as a formatting expression
    context = Context({'cmdOut': sr})
    out_str = context.get_formatted_value(
        'begin {cmdOut.returncode} {cmdOut.stdout} {cmdOut.stderr} end')
    assert out_str == 'begin 123 out err end'

    out_str = context.get_formatted_value(
        'begin {cmdOut[returncode]} {cmdOut[stdout]} {cmdOut[stderr]} end')
    assert out_str == 'begin 123 out err end'

    # works in a PyString
    assert context.get_formatted_value(PyString("cmdOut.returncode")) == 123
    assert context.get_formatted_value(PyString("cmdOut['returncode']")) == 123


def test_subprocessresult_repr():
    """Convert between SubprocessResult repr and instance."""
    sr = repr(SubprocessResult('mycmd', 123))
    rehydrated = eval(sr)
    assert rehydrated.cmd == 'mycmd'
    assert rehydrated.returncode == 123
    assert rehydrated.stdout is None
    assert rehydrated.stderr is None

    sr = repr(SubprocessResult('mycmd', 123, stdout=b'stdout'))
    rehydrated = eval(sr)
    assert rehydrated.cmd == 'mycmd'
    assert rehydrated.returncode == 123
    assert rehydrated.stdout == b'stdout'
    assert rehydrated.stderr is None

    sr = repr(SubprocessResult('mycmd', 123, stderr='err'))
    rehydrated = eval(sr)
    assert rehydrated.cmd == 'mycmd'
    assert rehydrated.returncode == 123
    assert rehydrated.stdout is None
    assert rehydrated.stderr == 'err'

    sr = repr(SubprocessResult('mycmd', 123, stdout='out', stderr='err'))
    rehydrated = eval(sr)
    assert rehydrated.cmd == 'mycmd'
    assert rehydrated.returncode == 123
    assert rehydrated.stdout == 'out'
    assert rehydrated.stderr == 'err'

    sr = repr(SubprocessResult(['my', 'cmd'], -123,
                               stdout=b'out', stderr=b'err'))
    rehydrated = eval(sr)
    assert rehydrated.cmd == ['my', 'cmd']
    assert rehydrated.returncode == -123
    assert rehydrated.stdout == b'out'
    assert rehydrated.stderr == b'err'


def test_subprocessresult_str():
    """Convert SubprocessResult to friendly string."""
    sr = str(SubprocessResult('mycmd', 123))
    assert sr == """\
cmd: mycmd
returncode: 123
stdout: None
stderr: None
"""

    sr = str(SubprocessResult('mycmd', 123, stdout=b'out'))
    assert sr == """\
cmd: mycmd
returncode: 123
stdout: b'out'
stderr: None
"""

    sr = str(SubprocessResult('mycmd', 123, stderr=b'err'))
    assert sr == """\
cmd: mycmd
returncode: 123
stdout: None
stderr: b'err'
"""

    sr = str(SubprocessResult('mycmd', 123, stdout=b'out', stderr='err'))
    assert sr == """\
cmd: mycmd
returncode: 123
stdout: b'out'
stderr: err
"""

    sr = str(SubprocessResult(['my', 'cmd'], -123,
                              stdout='out', stderr='err'))
    assert sr == """\
cmd: ['my', 'cmd']
returncode: -123
stdout: out
stderr: err
"""
# endregion SubprocessResult
