"""pypyr.dsl.cmdasync unit tests."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
import asyncio
import asyncio.subprocess
import locale
from pathlib import Path
from unittest import TestCase
from unittest.mock import call, DEFAULT, Mock, mock_open, patch

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError,
                          MultiError,
                          SubprocessError)
from pypyr.steps.dsl.cmdasync import AsyncCmdStep
from pypyr.aio.subproc import Command

PIPE = asyncio.subprocess.PIPE
LOCALE_ENCODING = locale.getpreferredencoding(False)

cmd_path = Path.cwd().joinpath('tests/testfiles/cmds')
is_windows = config.is_windows
is_posixy = not is_windows


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    return win if is_windows else posix

# region validation errors


def test_dsl_async_cmd_name_required():
    """Cmd Step requires name."""
    with pytest.raises(AssertionError):
        AsyncCmdStep(None, None)


def test_dsl_async_cmd_context_required():
    """Cmd Step requires context."""
    with pytest.raises(AssertionError):
        AsyncCmdStep('blah', None)


def test_dsl_async_cmd_context_cmd_required():
    """Cmd Step requires cmds in context."""
    with pytest.raises(KeyNotInContextError) as err:
        AsyncCmdStep('blah', Context({'a': 'b'}))

    assert str(err.value) == ("context['cmds'] doesn't exist. It must exist "
                              "for blah.")


def test_dsl_async_cmd_context_cmd_not_none():
    """Cmd Step requires cmds in context."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        AsyncCmdStep('blah', Context({'cmds': None}))

    assert str(err.value) == "context['cmds'] must have a value for blah."


def test_dsl_async_cmd_context_cmd_not_dict():
    """Cmd Step requires cmds in context to be a dict if not str."""
    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', Context({'cmds': 1}))

    assert str(err.value) == (
        """\
blah cmds config should be either a list:
cmds:
  - ./my-executable --arg
  - subdir/executable --arg1

or a dictionary with a `run` sub-key:
cmds:
  run:
    - ./my-executable --arg
    - subdir/executable --arg1
  cwd: ./mydir

Any of the list items in root can be in expanded syntax:
cmds:
  - ./my-executable --arg
  - subdir/executable --arg1
  - run:
      - ./arb-executable1 --arg value1
      - [./arb-executable2.1, ./arb-executable2.2]
    cwd: ../mydir/subdir
  - [./arb-executable3.1, ./arb-executable3.2]""")


def test_dsl_async_cmd_list_must_be_str_or_dict():
    """Each list input must be a string or a dict."""
    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', Context({'cmds': ['cmd1', 123]}))

    assert str(err.value) == ("""\
123 in blah cmds config is wrong.
Each list item should be either a simple string, or a list to run in serial,
or a dict for expanded syntax:
cmds:
  - ./my-executable --arg
  - run:
      - ./another-executable --arg value
      - ./another-executable --arg value2
    cwd: ../mydir/subdir
  - run:
      - ./arb-executable1 --arg value1
      - [./arb-executable2.1, ./arb-executable2.2]
    cwd: ../mydir/arbdir
  - [./arb-executable3.1, ./arb-executable3.2]""")


def test_dsl_async_cmd_dict_run_must_exist():
    """Dict input run must exist."""
    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', Context({'cmds': {'runs': 'abc'}}))

    # noqa is for line too long
    assert str(err.value) == ("""\
cmds.run doesn't exist for blah.
The input should look like this in expanded syntax:
cmds:
  run:
    - ./my-executable --arg
    - subdir/executable --arg1
  cwd: ./mydir

If you're passing in a list of commands, each command should be a simple string,
or a sub-list of commands to run in serial,
or a dict with a `run` entry:
cmds:
  - ./my-executable --arg
  - run: ./another-executable --arg value
    cwd: ../mydir/subdir
  - run:
      - ./arb-executable1 --arg value1
      - [./arb-executable2.1, ./arb-executable2.2]
    cwd: ../mydir/arbdir
  - [./arb-executable3.1, ./arb-executable3.2]""")  # noqa: E501


def test_dsl_async_cmd_dict_run_must_have_value():
    """Dict input run must have value."""
    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', Context({'cmds': {'run': ''}}))

    assert str(err.value) == ("""\
cmds.run must have a value for blah.
The `run` input should look something like this:
cmds:
  run:
    - ./arb-executable1 --arg value1
    - ./arb-executable2 --arg value2
  cwd: ../mydir/arbdir""")


def test_dsl_async_cmd_must_be_str_or_list():
    """Input to cmd must be a str or a list."""
    with pytest.raises(MultiError) as err:
        cmd = AsyncCmdStep('blah', Context({'cmds': {'run': 123}}))
        cmd.run_step()

    assert str(err.value) == ("""\
The following error(s) occurred while running the async commands:
ContextError: 123 cmds input.
Each command should be a simple string, or a sub-list to run in serial:
cmds:
  - ./my-executable --arg
  - ./another-executable --arg
  - [./executableA.1, ./executableA.2]

Or in the expanded syntax, set `run` to a list:
cmds:
  run:
    - ./my-executable --arg
    - ./another-executable --arg
    - [./executableA.1, ./executableA.2]
  cwd: ./mydir""")


def test_dsl_async_cmd_run_save_with_stdout_stderr():
    """Raise err when setting stdout | stderr alongside save."""
    context = Context({
        'cmds': {
            'run': ['A', 'B'],
            'save': True,
            'stdout': '/arb1',
            'stderr': '/arb2'}
    })

    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', context)

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")


def test_dsl_async_cmd_run_save_with_stdout():
    """Raise err when setting stdout | stderr alongside save."""
    context = Context({
        'cmds': {
            'run': ['A', 'B'],
            'save': True,
            'stdout': '/arb1'}
    })

    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', context)

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")


def test_dsl_async_run_save_with_stdout_or_stderr():
    """Raise err when setting stdout | stderr alongside save - or not and."""
    context = Context({
        'cmds': {
            'run': ['A', 'B'],
            'save': True,
            'stderr': '/arb2'}
    })

    with pytest.raises(ContextError) as err:
        AsyncCmdStep('blah', context)

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")

# endregion validation errors

# region minimal/maximal inputs


def test_async_cmd_minimal():
    """Minimal inputs."""
    context = Context({'cmds': ['A', 'B']})

    step = AsyncCmdStep('blah', context)

    assert len(step.commands) == 2
    cmd1 = step.commands[0]
    assert cmd1.cmd == 'A'
    assert cmd1.is_shell is False
    assert cmd1.cwd is None
    assert cmd1.is_save is False
    assert cmd1.is_text is False
    assert cmd1.stdout is None
    assert cmd1.stderr is None
    assert cmd1.encoding == LOCALE_ENCODING
    assert cmd1.append is False


def test_async_cmd_minimal_save():
    """Minimal inputs when save True."""
    context = Context({'cmds': {'run': ['A', 'B'], 'save': True}})

    step = AsyncCmdStep('blah', context)

    assert len(step.commands) == 1
    cmd1 = step.commands[0]
    assert cmd1.cmd == ['A', 'B']
    assert cmd1.is_shell is False
    assert cmd1.cwd is None
    assert cmd1.is_save is True
    assert cmd1.is_text is True
    assert cmd1.stdout == PIPE
    assert cmd1.stderr == PIPE
    assert cmd1.encoding == LOCALE_ENCODING
    assert cmd1.append is False


def test_async_cmd_maximal_save():
    """Maximal inputs with save true."""
    context = Context({'cmds': {
        'run': ['A', 'B'],
        'cwd': '/cwd',
        'save': True,
        'encoding': 'enc',
        'bytes': True}})

    step = AsyncCmdStep('blah', context)

    assert len(step.commands) == 1
    cmd1 = step.commands[0]
    assert cmd1.cmd == ['A', 'B']
    assert cmd1.is_shell is False
    assert cmd1.is_text is False
    assert cmd1.cwd == '/cwd'
    assert cmd1.is_save is True
    assert cmd1.stdout == PIPE
    assert cmd1.stderr == PIPE
    assert cmd1.encoding == 'enc'
    assert cmd1.append is False


def test_async_cmd_maximal_not_save():
    """Maximal inputs with save false."""
    context = Context({'cmds': {
        'run': ['A', 'B'],
        'cwd': '/cwd',
        'stdout': '/stdout',
        'stderr': '/stderr',
        'encoding': 'enc',
        'bytes': True,
        'append': True}})

    step = AsyncCmdStep('blah', context)

    assert len(step.commands) == 1
    cmd1 = step.commands[0]
    assert cmd1.cmd == ['A', 'B']
    assert cmd1.is_shell is False
    assert cmd1.is_text is False
    assert cmd1.cwd == '/cwd'
    assert cmd1.is_save is False
    assert cmd1.stdout == '/stdout'
    assert cmd1.stderr == '/stderr'
    assert cmd1.encoding == 'enc'
    assert cmd1.append is True


def test_async_cmd_maximal_save_formatting():
    """Maximal inputs with save true with formatting expressions."""
    context = Context({
        'cmdA': 'A',
        'cmdB': 'B',
        'cwd': '/cwd',
        'save': True,
        'enc': 'enc',
        'bytes': True,
        'cmds': {
            'run': ['{cmdA}', '{cmdB}'],
            'cwd': '{cwd}',
            'save': '{save}',
            'encoding': '{enc}',
            'bytes': '{bytes}'}})

    step = AsyncCmdStep('blah', context)

    assert len(step.commands) == 1
    cmd1 = step.commands[0]
    assert cmd1.cmd == ['A', 'B']
    assert cmd1.is_shell is False
    assert cmd1.is_text is False
    assert cmd1.cwd == '/cwd'
    assert cmd1.is_save is True
    assert cmd1.stdout == PIPE
    assert cmd1.stderr == PIPE
    assert cmd1.encoding == 'enc'
    assert cmd1.append is False


def test_async_cmd_maximal_not_save_formatting():
    """Maximal inputs with save false with formatting expressions."""
    context = Context({
        'cmdinput': ['A', 'B'],
        'cwd': '/cwd',
        'save': True,
        'enc': 'enc',
        'bytes': True,
        'stdout': '/stdout',
        'stderr': '/stderr',
        'append': True,
        'cmds': {
            'run': '{cmdinput}',
            'cwd': '{cwd}',
            'stdout': '{stdout}',
            'stderr': '{stderr}',
            'encoding': '{enc}',
            'bytes': '{bytes}',
            'append': '{append}'}})

    step = AsyncCmdStep('blah', context)

    assert len(step.commands) == 1
    cmd1 = step.commands[0]
    assert cmd1.cmd == ['A', 'B']
    assert cmd1.is_shell is False
    assert cmd1.is_text is False
    assert cmd1.cwd == '/cwd'
    assert cmd1.is_save is False
    assert cmd1.stdout == '/stdout'
    assert cmd1.stderr == '/stderr'
    assert cmd1.encoding == 'enc'
    assert cmd1.append is True

# endregion minimal/maximal inputs

# region test input combos w mocked subprocess call

# region AsyncMock plumbing


class AsyncMock(Mock):
    """Mock that acts like a coroutine/awaitable/future.

    As of py3.8, could use the built-in AsyncMock from unittest. But, still
    have to cater to py3.7, so stuck with this, yay.
    """

    async def __call__(self, *args, **kwargs):
        """Make the mock awaitable."""
        return super().__call__(*args, **kwargs)


def get_async_subproc_future(expected: list[asyncio.subprocess.Process]):
    """Return awaitable mock with canned responses/results."""
    return AsyncMock(side_effect=expected)


def expected_result(rc, stdout, stderr):
    """Return a mock of Process with preconfigured output for communicate()."""
    process = Mock(spec=asyncio.subprocess.Process)
    process.returncode = rc
    process.communicate = AsyncMock(return_value=(stdout, stderr))
    return process


ASYNC_SUBPROCESS_EXEC = 'pypyr.aio.subproc.asyncio.create_subprocess_exec'
ASYNC_SUBPROCESS_SHELL = 'pypyr.aio.subproc.asyncio.create_subprocess_shell'

# endregion AsyncMock plumbing


def test_async_cmd_simple_list():
    """Simple syntax list pass through with split vs no split on shlex."""
    context = Context({'cmds': ['A', 'B arg1 "arg 2"', 'C']})
    step = AsyncCmdStep('blah', context)

    assert step.commands.commands == [Command('A'),
                                      Command('B arg1 "arg 2"'),
                                      Command('C')]

    fake_subproc = get_async_subproc_future(
        [expected_result(0, None, None)] * 3)

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=None, stderr=None, cwd=None),
        call('B', 'arg1', 'arg 2', stdout=None, stderr=None, cwd=None),
        call('C', stdout=None, stderr=None, cwd=None)])

    assert 'cmdOut' not in context


def test_async_cmd_simple_str():
    """Simple syntax str for single item."""
    context = Context({'cmds': 'A'})
    step = AsyncCmdStep('blah', context)

    assert step.commands.commands == [Command('A')]

    fake_subproc = get_async_subproc_future([expected_result(0, None, None)])

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    assert mock_subproc.mock_calls == [
        call('A', stdout=None, stderr=None, cwd=None)]

    assert 'cmdOut' not in context


def test_async_shell_simple_list():
    """Simple syntax list pass through with split vs no split on shlex."""
    context = Context({'cmds': ['A', 'B arg1 "arg 2"', 'C']})
    step = AsyncCmdStep('blah', context, is_shell=True)

    assert step.commands.commands == [Command('A', is_shell=True),
                                      Command('B arg1 "arg 2"', is_shell=True),
                                      Command('C', is_shell=True)]

    fake_subproc = get_async_subproc_future(
        [expected_result(0, None, None)] * 3)

    with patch(ASYNC_SUBPROCESS_SHELL, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=None, stderr=None, cwd=None),
        call('B arg1 "arg 2"', stdout=None, stderr=None, cwd=None),
        call('C', stdout=None, stderr=None, cwd=None)])

    assert 'cmdOut' not in context


def test_async_list_with_dict():
    """Simple syntax list with any item a dict."""
    context = Context({'cmds': [
        'A',
        {'run': ['B', 'C']},
        {'run': ['D', ['E.1', 'E.2'], 'F']},
        'G']})
    step = AsyncCmdStep('blah', context)

    assert step.commands.commands == [Command('A'),
                                      Command(['B', 'C']),
                                      Command(['D', ['E.1', 'E.2'], 'F']),
                                      Command('G')]

    fake_subproc = get_async_subproc_future(
        [expected_result(0, None, None)] * 8)

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    # sadly can't really confirm that the serial calls happened serially here
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=None, stderr=None, cwd=None),
        call('B', stdout=None, stderr=None, cwd=None),
        call('C', stdout=None, stderr=None, cwd=None),
        call('D', stdout=None, stderr=None, cwd=None),
        call('E.1', stdout=None, stderr=None, cwd=None),
        call('E.2', stdout=None, stderr=None, cwd=None),
        call('F', stdout=None, stderr=None, cwd=None),
        call('G', stdout=None, stderr=None, cwd=None)])

    assert 'cmdOut' not in context


def test_async_simple_list_with_serial():
    """Simple syntax list with sub-list for serial."""
    context = Context({'cmds': ['A', ['B.1', 'B.2'], ['C.1', 'C.2'], 'D']})
    step = AsyncCmdStep('blah', context)

    assert step.commands.commands == [Command('A'),
                                      Command([['B.1', 'B.2']]),
                                      Command([['C.1', 'C.2']]),
                                      Command('D')]

    fake_subproc = get_async_subproc_future(
        [expected_result(0, None, None)] * 6)

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    # sadly can't really confirm that the serial calls happened serially here
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=None, stderr=None, cwd=None),
        call('D', stdout=None, stderr=None, cwd=None),
        call('B.1', stdout=None, stderr=None, cwd=None),
        call('B.2', stdout=None, stderr=None, cwd=None),
        call('C.1', stdout=None, stderr=None, cwd=None),
        call('C.2', stdout=None, stderr=None, cwd=None)])

    assert 'cmdOut' not in context


def test_async_dict_run_list_with_serial():
    """Expanded syntax run list with sub-list for serial."""
    context = Context({'cmds': {'run':
                                ['A', ['B.1', 'B.2'], ['C.1', 'C.2'], 'D']}})
    step = AsyncCmdStep('blah', context)

    assert step.commands.commands == [Command(['A',
                                      ['B.1', 'B.2'],
                                      ['C.1', 'C.2'],
                                      'D'
                                      ])]

    fake_subproc = get_async_subproc_future(
        [expected_result(0, None, None)] * 6)

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    # sadly can't really confirm that the serial calls happened serially here
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=None, stderr=None, cwd=None),
        call('D', stdout=None, stderr=None, cwd=None),
        call('B.1', stdout=None, stderr=None, cwd=None),
        call('B.2', stdout=None, stderr=None, cwd=None),
        call('C.1', stdout=None, stderr=None, cwd=None),
        call('C.2', stdout=None, stderr=None, cwd=None)])

    assert 'cmdOut' not in context

# region save


def test_dsl_async_cmd_shell_override():
    """Override shell arg from dict shell input."""
    obj = AsyncCmdStep('blahname', Context({'cmds': {'run': 'blah',
                                                     'cwd': 'pathhere',
                                                     'shell': True,
                                                     }}),
                       is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert len(obj.commands.commands) == 1
    cmd = obj.commands.commands[0]
    assert cmd.is_shell
    assert not cmd.is_save


def test_async_cmd_with_save():
    """Save with simple list."""
    context = Context({'cmds': {'run': ['A', '"B with space" --arg', 'C'],
                                'save': True}})
    step = AsyncCmdStep('blah', context)

    assert step.commands.commands == [Command(['A',
                                      '"B with space" --arg',
                                               'C'], is_save=True)]

    fake_subproc = get_async_subproc_future([
        expected_result(0, b'out1', b'err1'),
        expected_result(0, b'out2', b'err2'),
        expected_result(0, b'out3', b'err3')])

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=PIPE, stderr=PIPE, cwd=None),
        call('B with space', '--arg', stdout=PIPE, stderr=PIPE, cwd=None),
        call('C', stdout=PIPE, stderr=PIPE, cwd=None)])

    out1 = context['cmdOut'][0]
    assert out1.cmd == ['A']
    assert out1.returncode == 0
    assert out1.stdout == 'out1'
    assert out1.stderr == 'err1'

    out2 = context['cmdOut'][1]
    assert out2.cmd == ['B with space', '--arg']
    assert out2.returncode == 0
    assert out2.stdout == 'out2'
    assert out2.stderr == 'err2'

    out3 = context['cmdOut'][2]
    assert out3.cmd == ['C']
    assert out3.returncode == 0
    assert out3.stdout == 'out3'
    assert out3.stderr == 'err3'


def test_async_shell_with_save():
    """Save with simple list."""
    context = Context({'cmds': {'run': ['A', '"B with space" --arg', 'C'],
                                'save': True}})
    step = AsyncCmdStep('blah', context, is_shell=True)

    assert step.commands.commands == [Command(['A',
                                      '"B with space" --arg',
                                               'C'],
                                              is_shell=True,
                                              is_save=True)]

    fake_subproc = get_async_subproc_future([
        expected_result(0, b'out1', b'err1'),
        expected_result(0, b'out2', b'err2'),
        expected_result(0, b'out3', b'err3')])

    with patch(ASYNC_SUBPROCESS_SHELL, fake_subproc) as mock_subproc:
        step.run_step()

    # despite name, checks equality for all items in ANY order
    TestCase().assertCountEqual(mock_subproc.mock_calls, [
        call('A', stdout=PIPE, stderr=PIPE, cwd=None),
        call('"B with space" --arg', stdout=PIPE, stderr=PIPE, cwd=None),
        call('C', stdout=PIPE, stderr=PIPE, cwd=None)])

    out1 = context['cmdOut'][0]
    assert out1.cmd == 'A'
    assert out1.returncode == 0
    assert out1.stdout == 'out1'
    assert out1.stderr == 'err1'

    out2 = context['cmdOut'][1]
    assert out2.cmd == '"B with space" --arg'
    assert out2.returncode == 0
    assert out2.stdout == 'out2'
    assert out2.stderr == 'err2'

    out3 = context['cmdOut'][2]
    assert out3.cmd == 'C'
    assert out3.returncode == 0
    assert out3.stdout == 'out3'
    assert out3.stderr == 'err3'


# endregion save

def test_async_cmds_fail_to_open_file_handle():
    """Catch error when file handle can't open."""
    context = Context({
        'cmds': {
            'run': ['cmd1', 'cmd2'],
            'stdout': '/stdout',
            'stderr': '/stderr'}
    })

    step = AsyncCmdStep('blah', context)

    with patch('pypyr.aio.subproc.open', mock_open()) as mock_fs:
        mock_fs.side_effect = [DEFAULT, FileNotFoundError('two')]

        with pytest.raises(MultiError) as err:
            with patch(ASYNC_SUBPROCESS_EXEC) as mock_subproc:
                step.run_step()

            mock_subproc.assert_not_called()

        the_err = err.value
        assert len(the_err) == 1
        assert str(the_err[0]) == 'two'

    results = step.commands[0].results
    assert len(results) == 1
    assert repr(results[0]) == "FileNotFoundError('two')"


def test_async_cmds_fail_to_open_file_handle_multiple_files():
    """Catch error when file handle can't open on multiple expanded."""
    context = Context({
        'cmds': [{
            'run': ['cmd1', 'cmd2'],
            'stdout': '/stdout',
            'stderr': '/stderr'},
            {
            'run': ['cmd3', 'cmd4'],
            'stdout': '/stdout2',
            'stderr': '/stderr2'}
        ]})

    step = AsyncCmdStep('blah', context)

    with patch('pypyr.aio.subproc.open', mock_open()) as mock_fs:
        mock_fs.side_effect = [DEFAULT,
                               FileNotFoundError('two'),
                               FileNotFoundError('three'),
                               DEFAULT]

        with pytest.raises(MultiError) as err:
            with patch(ASYNC_SUBPROCESS_EXEC) as mock_subproc:
                step.run_step()

            mock_subproc.assert_not_called()

        the_err = err.value
        assert len(the_err) == 2
        assert str(the_err[0]) == 'two'
        assert str(the_err[1]) == 'three'

    assert len(step.commands) == 2
    results = step.commands[0].results
    assert len(results) == 1
    assert repr(results[0]) == "FileNotFoundError('two')"

    results = step.commands[1].results
    assert len(results) == 1
    assert repr(results[0]) == "FileNotFoundError('three')"


def test_async_cmd_serial_simple_sequence():
    """Serial happens one after the other."""
    context = Context({'cmds': ['A', ['B.1', 'B.2'], 'C']})

    step = AsyncCmdStep('blah', context)

    fake_subproc = get_async_subproc_future([
        expected_result(0, b'outA', b'errA'),
        expected_result(0, b'outB.1', b'errB.1'),
        expected_result(0, b'outC', b'errC'),
        expected_result(0, b'outB.2', b'errB.2'), ])

    with patch(ASYNC_SUBPROCESS_EXEC, fake_subproc) as mock_subproc:
        step.run_step()

    assert len(mock_subproc.mock_calls) == 4
    TestCase().assertCountEqual(mock_subproc.mock_calls[:3], [
        call('A', stdout=None, stderr=None, cwd=None),
        call('B.1', stdout=None, stderr=None, cwd=None),
        call('C', stdout=None, stderr=None, cwd=None)
    ])

    assert mock_subproc.mock_calls[3] == call('B.2',
                                              stdout=None, stderr=None,
                                              cwd=None)
    assert 'cmdOut' not in context
# endregion test input combos w mocked subprocess call

# region actual subprocess spawning


def test_dsl_async_cmd_str_with_spaces_in_path():
    """Single command string works with spaces in path."""
    cmd = get_cmd('tests/testfiles/cmds/"file with space.sh"',
                  r'tests\testfiles\cmds\file with space.bat')
    context = Context({'a': 'one two',
                       'd': cmd,
                      'cmds': '{d} "{a}"'})

    step = AsyncCmdStep('blah', context)
    step.run_step()

    assert 'cmdOut' not in context

    # and with quotes
    if is_windows:
        context = Context({
            'cmds': r'"tests\testfiles\cmds\file with space.bat" "one two"'})
        step = AsyncCmdStep('blah', context)
        step.run_step()

        assert 'cmdOut' not in context


def test_dsl_async_cmd_error_throws():
    """Process returning 1 should throw CalledProcessError with no save."""
    cmd1 = get_cmd('tests/testfiles/cmds/exit1.sh',
                   r'tests\testfiles\cmds\exit1.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                   r'tests\testfiles\cmds\exitwitherr.bat')

    context = Context({'cmds': [cmd1, cmd2]})
    step = AsyncCmdStep('blah', context)

    with pytest.raises(MultiError) as multi_err:
        step.run_step()

    assert 'cmdOut' not in context

    errs = multi_err.value
    assert len(errs) == 2

    err1 = errs[0]
    assert type(err1) is SubprocessError
    assert err1.cmd == [cmd1]

    err2 = errs[1]
    assert type(err2) is SubprocessError
    assert err2.cmd == [cmd2]


def test_dsl_async_cmd_error_throws_exception_initiating_spawn():
    """Exception when can't run the subprocess at all."""
    cmd1 = get_cmd('tests/testfiles/cmds/xxx1',
                   r'tests\testfiles\cmds\xxx1')

    cmd2 = get_cmd('tests/testfiles/cmds/xxx2',
                   r'tests\testfiles\cmds\xxx2')

    cmd3 = get_cmd('tests/testfiles/cmds/exit1.sh',
                   r'tests\testfiles\cmds\exit1.bat')

    context = Context({'cmds': [cmd1, cmd2, cmd3]})
    step = AsyncCmdStep('blah', context)

    with pytest.raises(MultiError) as multi_err:
        step.run_step()

    assert 'cmdOut' not in context

    errs = multi_err.value
    assert len(errs) == 3
    err1 = errs[0]
    assert type(err1) is FileNotFoundError
    if is_posixy:
        assert err1.filename == cmd1

    err2 = errs[1]
    assert type(err2) is FileNotFoundError
    if is_posixy:
        assert err2.filename == cmd2

    err3 = errs[2]
    assert type(err3) is SubprocessError
    assert err3.returncode == 1
    assert err3.cmd == [cmd3]


def test_dsl_async_cmd_error_throws_with_save_true():
    """Process returning 1 should throw CalledProcessError."""
    cmd = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                  r'tests\testfiles\cmds\exitwitherr.bat')

    context = Context({'cmds': {'run': cmd, 'save': True}})

    step = AsyncCmdStep('blah', context)

    with pytest.raises(MultiError):
        step.run_step()

    out = context['cmdOut']
    assert len(out) == 1
    result = out[0]
    assert result.returncode == 1
    assert not result.stdout
    assert result.stderr == 'arb err here'


def test_dsl_async_cmd_error_spawning_throws_with_save_true():
    """Raise FileNotFoundError when cannot initiate the subprocess."""
    cmd = get_cmd('tests/testfiles/cmds/xxxx1',
                  r'tests\testfiles\cmds\xxxx1')

    context = Context({'cmds': {'run': [cmd], 'save': True}})

    step = AsyncCmdStep('blah', context)

    with pytest.raises(MultiError):
        step.run_step()

    out = context['cmdOut']
    assert len(out) == 1
    result = out[0]
    assert type(result) is FileNotFoundError
    if is_posixy:
        assert result.filename == cmd


def test_dsl_async_cmd_run_has_list_input_with_complex_args():
    """List input to run complex dict works with multiple args."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'one',
                       'b': 'two two',
                      'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmds': {
                           'run': [
                               '{d} {a} "{b}" {c}',
                               '{e} four "five six" seven'],
                            'save': False}
                       })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    assert 'cmdOut' not in context


def test_dsl_async_cmd_list_input_with_simple_cmd_strings():
    """List input with command string works with multiple args."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'one',
                       'b': 'two two',
                      'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmds': [
                           '{d} {a} "{b}" {c}',
                           '{e} four "five six" seven']})

    step = AsyncCmdStep('blah', context)
    step.run_step()

    assert 'cmdOut' not in context


def test_dsl_async_cmd_list_input_with_complex_args():
    """List input mixing command string & dict works with multiple args."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'one',
                       'b': 'two two',
                      'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmds': [
                           {'run': '{d} {a} "{b}" {c}',
                            'save': False},
                           '{e} four "five six" seven']})

    step = AsyncCmdStep('blah', context)
    step.run_step()

    assert 'cmdOut' not in context


def test_dsl_async_cmd_list_input_with_simple_cmd_strings_error_on_first():
    """List input with command string works runs all but raises err on one."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('echo blah',
                   r'tests\testfiles\cmds\echo.bat blah')

    context = Context({'a': 'WRONG VALUE',
                       'b': 'two two',
                      'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmds': [
                           '{d} {a} "{b}" {c}',
                           '{e}']})
    step = AsyncCmdStep('blah', context)

    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value) == 1
    the_err = err.value[0]

    assert the_err.cmd == [cmd1, 'WRONG', 'VALUE', 'two two', 'three']

    assert 'cmdOut' not in context
    assert len(step.commands) == 2
    cmd2_results = step.commands[1].results
    assert len(cmd2_results) == 1
    assert cmd2_results[0].cmd == cmd2.split()
    assert cmd2_results[0].returncode == 0


def test_dsl_async_cmd_list_input_with_complex_args_error_on_first():
    """List input mixing command string & dict raises err on one."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'WRONG',
                       'b': 'two two',
                      'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmds': [
                           {'run': '{d} {a} "{b}" {c}',
                            'save': False},
                           '{e} four "five six" seven']})

    step = AsyncCmdStep('blah', context)
    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value) == 1
    the_err = err.value[0]

    assert the_err.cmd == [cmd1, 'WRONG', 'two two', 'three']

    assert 'cmdOut' not in context
    assert len(step.commands) == 2
    cmd2_results = step.commands[1].results
    assert len(cmd2_results) == 1
    assert cmd2_results[0].cmd == [cmd2, 'four', 'five six', 'seven']
    assert cmd2_results[0].returncode == 0


def test_dsl_async_cmd_dict_input_sequence_with_cwd_interpolate():
    """Cwd plus interpolation."""
    if is_windows:
        # windows path supports front slashes IF it's absolute
        cmd = cmd_path.joinpath('pwd.bat').as_posix()
    else:
        # deliberately testing relative path resolution here
        cmd = 'testfiles/cmds/pwd.sh'

    context = Context({'k1': 'tests',
                       'cmds': {'run': cmd,
                                'save': True,
                                'cwd': '{k1}'}})

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 1
    result = out[0]
    assert result.returncode == 0
    assert Path(result.stdout).samefile('./tests')
    assert not result.stderr
# region is_save


def test_dsl_async_cmd_list_input_with_complex_args_error_only_first_save():
    """List input mixing command str & dict, all error but 1st save output."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'WRONG',
                       'b': 'two two',
                      'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmds': [
                           {'run': '{d} {a} "{b}" {c}',
                            'save': True},
                           '{e} WRONG "five six" seven']})

    step = AsyncCmdStep('blah', context)

    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value) == 2
    err1 = err.value[0]

    assert err1.cmd == [cmd1, 'WRONG', 'two two', 'three']
    assert err1.returncode == 1
    assert err1.stdout == b''
    assert err1.stderr == 'assert failed'

    err2 = err.value[1]

    # save is only true for 1st one, thus no stdout/stderr
    assert err2.cmd == [cmd2, 'WRONG', 'five six', 'seven']
    assert err2.returncode == 1
    assert err2.stdout is None
    assert err2.stderr is None

    # only the cmd with save True ends up in cmdOut
    out = context['cmdOut']
    assert len(out) == 1
    out1 = out[0]
    assert out1.cmd == [cmd1, 'WRONG', 'two two', 'three']
    assert out1.returncode == 1
    assert out1.stdout == b''
    assert out1.stderr == 'assert failed'


def test_dsl_async_cmd_run_has_list_input_save():
    """List input to run complex dict save all output."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo "two three"',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    context = Context({
        'cmds': {
            'run': [cmd1, cmd2],
            'save': True}
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 2
    out1 = out[0]
    assert out1.returncode == 0
    assert out1.stdout == 'one'
    assert not out1.stderr

    out2 = out[1]
    assert out2.returncode == 0
    assert out2.stdout == 'two three'
    assert not out2.stderr


def test_dsl_async_cmd_list_with_multiple_runs_save():
    """List input with run in expanded, everything save to results."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two',
                   r'tests\testfiles\cmds\echo.bat two')

    cmd3 = get_cmd('echo three',
                   r'tests\testfiles\cmds\echo.bat three')

    cmd4 = get_cmd('echo four',
                   r'tests\testfiles\cmds\echo.bat four')

    cmd5 = get_cmd('echo five',
                   r'tests\testfiles\cmds\echo.bat five')

    context = Context({
        'cmds': [
            {'run': [cmd1, cmd2],
             'save': True},
            {'run': [cmd3, cmd4],
             'save': True},
            cmd5,
        ]
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 4

    out1 = out[0]
    assert out1.returncode == 0
    assert out1.stdout == 'one'
    assert not out1.stderr

    out2 = out[1]
    assert out2.returncode == 0
    assert out2.stdout == 'two'
    assert not out2.stderr

    out3 = out[2]
    assert out3.returncode == 0
    assert out3.stdout == 'three'
    assert not out3.stderr

    out4 = out[3]
    assert out4.returncode == 0
    assert out4.stdout == 'four'
    assert not out4.stderr


def test_dsl_async_cmd_run_has_list_input_save_dev_null():
    """List input to run complex dict save all output to /dev/null."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two three',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    context = Context({
        'cmds': {
            'run': [cmd1, cmd2],
            'stdout': '/dev/null',
            'stderr': '/dev/null'}
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    assert 'cmdOut' not in context

# region encoding


powershell = "powershell -ExecutionPolicy Bypass -NoLogo -NoProfile"


def test_dsl_async_cmd_run_save_with_encoding():
    """Encoding works."""
    if is_windows:
        cmd = f"{powershell} ./tests/testfiles/cmds/bytes-out.ps1"
        encoding = 'utf-16le'
    else:
        cmd = 'tests/testfiles/cmds/bytes-out.sh'
        encoding = 'utf-16'

    context = Context({
        'cmds': {
            'run': [cmd],
            'save': True,
            'encoding': encoding}
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 1

    result = context['cmdOut'][0]
    assert result.returncode == 0
    assert result.stdout == 'one two three'
    assert result.stderr == 'four'


def test_dsl_async_cmd_run_save_with_binary_mode():
    """Binary mode does not strip lf."""
    if is_windows:
        # the literal \ escaping the " is NB
        ps_cmd = """\
$out=[System.Text.Encoding]::Unicode.GetBytes(\\"one`n\\");
[System.Console]::OpenStandardOutput().Write($out, 0, $out.Length);
$err=[System.Text.Encoding]::Unicode.GetBytes(\\"two`n\\");
[System.Console]::OpenStandardError().Write($err, 0, $err.Length);"""

        cmd = f'powershell -NoLogo -NoProfile -Command {ps_cmd}'
    else:
        cmd = 'tests/testfiles/cmds/bytes-out-lf.sh'

    context = Context({
        'cmds': {
            'run': cmd,
            'save': True,
            'bytes': True}
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 1

    result = context['cmdOut'][0]
    assert result.returncode == 0
    assert result.stdout.decode('utf-16') == 'one\n'
    assert result.stderr.decode('utf-16') == 'two\n'
# endregion encoding

# region serial


def test_dsl_async_cmd_serial_simple_syntax_save():
    """Serial with concurrent with save."""
    echo = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh',
                   r'tests\testfiles\cmds\echo-out-and-err.bat')

    context = Context({
        'cmds': {
            'run': [f'{echo} A', [f'{echo} B.1', f'{echo} B.2'], f'{echo} C'],
            'save': True}
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 3

    outA = out[0]
    assert outA.stdout == 'stdout A'
    assert outA.stderr == 'stderr A'

    outB = out[1]
    assert len(outB) == 2
    outB1 = outB[0]
    assert outB1.stdout == 'stdout B.1'
    assert outB1.stderr == 'stderr B.1'

    outB2 = outB[1]
    assert outB2.stdout == 'stdout B.2'
    assert outB2.stderr == 'stderr B.2'

    outC = out[2]
    assert outC.stdout == 'stdout C'
    assert outC.stderr == 'stderr C'


def test_dsl_async_cmd_serial_multiple_expanded_syntax_save():
    """Serial with concurrent with save."""
    echo = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh',
                   r'tests\testfiles\cmds\echo-out-and-err.bat')

    context = Context({
        'cmds': [{
            'run': [f'{echo} A', [f'{echo} B.1', f'{echo} B.2'], f'{echo} C'],
            'save': True},
            {
            'run': [[f'{echo} D.1', f'{echo} D.2']],
            'save': True}
        ]
    })

    step = AsyncCmdStep('blah', context)
    step.run_step()

    out = context['cmdOut']
    assert len(out) == 4

    outA = out[0]
    assert outA.stdout == 'stdout A'
    assert outA.stderr == 'stderr A'

    outB = out[1]
    assert len(outB) == 2
    outB1 = outB[0]
    assert outB1.stdout == 'stdout B.1'
    assert outB1.stderr == 'stderr B.1'

    outB2 = outB[1]
    assert outB2.stdout == 'stdout B.2'
    assert outB2.stderr == 'stderr B.2'

    outC = out[2]
    assert outC.stdout == 'stdout C'
    assert outC.stderr == 'stderr C'

    outD = out[3]
    assert len(outD) == 2
    outD1 = outD[0]
    assert outD1.stdout == 'stdout D.1'
    assert outD1.stderr == 'stderr D.1'

    outD2 = outD[1]
    assert outD2.stdout == 'stdout D.2'
    assert outD2.stderr == 'stderr D.2'


def test_dsl_async_cmd_serial_simple_syntax_save_with_error_spawning():
    """Serial does not continue after error spawning subprocess."""
    echo = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh',
                   r'tests\testfiles\cmds\echo-out-and-err.bat')

    cmd_not_found = get_cmd('tests/testfiles/cmds/xxx1',
                            r'tests\testfiles\cmds\xxx1')
    context = Context({
        'cmds': {
            'run': [f'{echo} A',
                    [f'{echo} B.1', cmd_not_found, f'{echo} B.3'],
                    f'{echo} C'],
            'save': True}
    })

    step = AsyncCmdStep('blah', context)
    with pytest.raises(MultiError):
        step.run_step()

    out = context['cmdOut']
    assert len(out) == 3

    outA = out[0]
    assert outA.stdout == 'stdout A'
    assert outA.stderr == 'stderr A'

    outB = out[1]
    assert len(outB) == 2
    outB1 = outB[0]
    assert outB1.stdout == 'stdout B.1'
    assert outB1.stderr == 'stderr B.1'

    outB2 = outB[1]
    assert type(outB2) is FileNotFoundError
    if is_posixy:
        assert outB2.filename == cmd_not_found

    outC = out[2]
    assert outC.stdout == 'stdout C'
    assert outC.stderr == 'stderr C'


def test_dsl_async_cmd_serial_simple_syntax_save_with_error_return_1():
    """Serial does not continue after subprocess return code is 1."""
    echo = get_cmd('tests/testfiles/cmds/echo-out-and-err.sh',
                   r'tests\testfiles\cmds\echo-out-and-err.bat')

    cmd_return_1 = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                           r'tests\testfiles\cmds\exitwitherr.bat')

    context = Context({
        'cmds': {
            'run': [f'{echo} A',
                    [f'{echo} B.1', cmd_return_1, f'{echo} B.3'],
                    f'{echo} C'],
            'save': True}
    })

    step = AsyncCmdStep('blah', context)
    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value) == 1
    the_err = err.value[0]
    assert the_err.cmd == [cmd_return_1]
    assert the_err.stderr == 'arb err here'

    out = context['cmdOut']
    assert len(out) == 3

    outA = out[0]
    assert outA.stdout == 'stdout A'
    assert outA.stderr == 'stderr A'

    outB = out[1]
    assert len(outB) == 2
    outB1 = outB[0]
    assert outB1.stdout == 'stdout B.1'
    assert outB1.stderr == 'stderr B.1'

    outB2 = outB[1]
    assert outB2.returncode == 1
    assert outB2.cmd == [cmd_return_1]
    assert not outB2.stdout
    assert outB2.stderr == 'arb err here'

    outC = out[2]
    assert outC.stdout == 'stdout C'
    assert outC.stderr == 'stderr C'
# endregion serial

# endregion is_save

# endregion actual subprocess spawning
