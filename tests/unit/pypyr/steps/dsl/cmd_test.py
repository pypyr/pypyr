"""cmd.py unit tests."""
import logging
import subprocess
from unittest.mock import call, patch

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.dsl import SicString
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.steps.dsl.cmd import CmdStep
from pypyr.subproc import Command

from tests.common.utils import patch_logger

is_windows = config.is_windows

sp_mod_name = 'pypyr.subproc'


def get_plat(posix, windows):
    """Return windows if platform is windows, else posix."""
    return windows if is_windows else posix


def test_cmdstep_name_required():
    """Cmd Step requires name."""
    with pytest.raises(AssertionError):
        CmdStep(None, None)


def test_cmdstep_context_required():
    """Cmd Step requires context."""
    with pytest.raises(AssertionError):
        CmdStep('blah', None)


def test_cmdstep_context_cmd_required():
    """Cmd Step requires cmd in context."""
    with pytest.raises(KeyNotInContextError) as err:
        CmdStep('blah', Context({'a': 'b'}))

    assert str(err.value) == ("context['cmd'] doesn't exist. It must exist "
                              "for blah.")


def test_cmdstep_context_cmd_not_none():
    """Cmd Step requires cmd in context."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        CmdStep('blah', Context({'cmd': None}))

    assert str(err.value) == "context['cmd'] must have a value for blah."


def test_cmdstep_context_cmd_not_dict():
    """Cmd Step requires cmd in context to be a dict if not str."""
    with pytest.raises(ContextError) as err:
        CmdStep('blah', Context({'cmd': 1}))

    assert str(err.value) == (
        """blah cmd config should be either a simple string:
cmd: my-executable --arg

or a dictionary:
cmd:
  run: subdir/my-executable --arg
  cwd: ./mydir

or a list of commands:
cmd:
  - my-executable --arg
  - run: another-executable --arg value
    cwd: ../mydir/subdir""")


def test_dsl_cmd_list_must_be_str_or_dict():
    """Each list input must be a string or a dict."""
    with pytest.raises(ContextError) as err:
        CmdStep('blah', Context({'cmd': ['cmd1', 123]}))

    assert str(err.value) == ("""\
123 in blah cmd config is wrong.
Each list item should be either a simple string or a dict for expanded syntax:
cmd:
  - my-executable --arg
  - run: another-executable --arg value
    cwd: ../mydir/subdir
  - run:
      - arb-executable1 --arg value1
      - arb-executable2 --arg value2
    cwd: ../mydir/arbdir""")


def test_dsl_cmd_dict_run_must_exist():
    """Dict input run must exist."""
    with pytest.raises(ContextError) as err:
        CmdStep('blah', Context({'cmd': {'runs': 'abc'}}))

    # noqa is for line too long
    assert str(err.value) == ("""\
cmd.run doesn't exist for blah.
The input should look like this in the simplified syntax:
cmd: my-executable-here --arg1

Or in the expanded syntax:
cmd:
  run: my-executable-here --arg1

If you're passing in a list of commands, each command should be a simple string,
or a dict with a `run` entry:
cmd:
  - my-executable --arg
  - run: another-executable --arg value
    cwd: ../mydir/subdir
  - run:
      - arb-executable1 --arg value1
      - arb-executable2 --arg value2
    cwd: ../mydir/arbdir""")  # noqa: E501


def test_dsl_cmd_dict_run_must_have_value():
    """Dict input run must have value."""
    with pytest.raises(ContextError) as err:
        CmdStep('blah', Context({'cmd': {'run': ''}}))

    assert str(err.value) == ("""\
cmd.run must have a value for blah.
The `run` input should look something like this:
cmd:
  run: my-executable-here --arg1
  cwd: ./mydir/subdir

Or, `run` could be a list of commands:
cmd:
  run:
    - arb-executable1 --arg value1
    - arb-executable2 --arg value2
  cwd: ../mydir/arbdir""")


def test_dsl_cmd_must_be_str_or_list():
    """Input to cmd must be a str or a list."""
    with pytest.raises(ContextError) as err:
        cmd = CmdStep('blah', Context({'cmd': {'run': 123}}))
        cmd.run_step()

    assert str(err.value) == ("""\
123 cmd should be either a simple string:
cmd: my-executable --arg

Or in the expanded syntax, set `run` to a string:

cmd:
  run: my-executable --arg
  cwd: ./mydir

Or set run to a list of commands:
cmd:
  run:
    - my-executable --arg
    - another-executable --arg2
  cwd: ../mydir/subdir""")


def test_cmdstep_cmd_is_string():
    """Str command is always not is_save."""
    obj = CmdStep('blahname', Context({'cmd': 'blah'}))

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah'})
    assert obj.commands == [Command('blah',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]


def test_cmdstep_cmd_is_dict_default_save_false():
    """Dict command defaults not is_save."""
    obj = CmdStep('blahname', Context({'cmd': {'run': 'blah'}}))

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah'}})
    assert obj.commands == [Command('blah',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]


def test_cmdstep_cmd_is_dict_default_save_true():
    """Dict command with is_save true."""
    obj = CmdStep('blahname', Context({'cmd': {'run': 'blah',
                                               'save': True}}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah', 'save': True}})
    assert obj.commands == [Command('blah',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=True)]


def test_cmdstep_cmd_is_dict_cwd():
    """Cwd assigns."""
    obj = CmdStep('blahname', Context({'cmd': {'run': 'blah',
                                               'cwd': 'pathhere'}}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah', 'cwd': 'pathhere'}})
    assert obj.commands == [Command('blah',
                                    cwd='pathhere',
                                    is_shell=False,
                                    is_save=False)]


def test_dsl_cmd_shell_override():
    """Override shell arg from dict shell input."""
    obj = CmdStep('blahname', Context({'cmd': {'run': 'blah',
                                               'cwd': 'pathhere',
                                               'shell': True,
                                               }}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert len(obj.commands) == 1
    cmd = obj.commands[0]
    assert cmd.is_shell
    assert not cmd.is_save


def test_cmdstep_cmd_is_dict_cwd_none():
    """Explicit None on cwd."""
    obj = CmdStep('blahname', Context({'cmd': {'run': 'blah',
                                               'cwd': None}}))

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah', 'cwd': None}})
    assert obj.commands == [Command('blah',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]


def test_cmdstep_runstep_cmd_is_string_shell_false():
    """Str command is always not is_save."""
    obj = CmdStep('blahname', Context({'cmd': 'blah -blah1 --blah2'}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah -blah1 --blah2'})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    expected_cmd = get_plat(['blah', '-blah1', '--blah2'],
                            'blah -blah1 --blah2')

    mock_run.assert_called_once_with(expected_cmd,
                                     cwd=None,
                                     shell=False,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_string_shell_false_force_no_win(monkeypatch):
    """Force not windows."""
    monkeypatch.setattr('pypyr.subproc.config._is_windows', False)

    obj = CmdStep('blahname', Context({'cmd': 'blah -blah1 --blah2'}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah -blah1 --blah2'})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    mock_run.assert_called_once_with(['blah', '-blah1', '--blah2'],
                                     cwd=None,
                                     shell=False,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_string_formatting_shell_false():
    """Str command is always not is_save and works with formatting."""
    obj = CmdStep('blahname', Context({'k1': 'blah',
                                       'cmd': '{k1} -{k1}1 --{k1}2'}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'cmd': '{k1} -{k1}1 --{k1}2'})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    expected_cmd = get_plat(['blah', '-blah1', '--blah2'],
                            'blah -blah1 --blah2')

    mock_run.assert_called_once_with(expected_cmd,
                                     cwd=None,
                                     shell=False,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_string_formatting_shell_false_sic():
    """Command process special tag directive."""
    obj = CmdStep('blahname',
                  Context({'k1': 'blah',
                           'cmd': SicString('{k1} -{k1}1 --{k1}2')}),
                  is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'cmd': SicString('{k1} -{k1}1 --{k1}2')})

    assert obj.commands == [Command('{k1} -{k1}1 --{k1}2',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: {k1} -{k1}1 --{k1}2')]

    expected_cmd = get_plat(['{k1}', '-{k1}1', '--{k1}2'],
                            '{k1} -{k1}1 --{k1}2')

    mock_run.assert_called_once_with(expected_cmd,
                                     cwd=None,
                                     shell=False,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_string_shell_true():
    """Str command is always not is_save."""
    obj = CmdStep('blahname',
                  Context({'cmd': 'blah -blah1 --blah2'}),
                  is_shell=True)

    assert obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah -blah1 --blah2'})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=True,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    # blah is in a list because shell == false
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     cwd=None,
                                     shell=True,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_string_formatting_shell_true():
    """Str command is always not is_save and works with formatting."""
    obj = CmdStep('blahname',
                  Context({'k1': 'blah',
                           'cmd': '{k1} -{k1}1 --{k1}2'}),
                  is_shell=True)

    assert obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'cmd': '{k1} -{k1}1 --{k1}2'})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=True,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    # blah is a string because shell == true
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     cwd=None,
                                     shell=True,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_dict_save_false_shell_false():
    """Dict command with save false and shell false."""
    obj = CmdStep('blahname', Context({'cmd': {
        'run': 'blah -blah1 --blah2'}}),
        is_shell=False)

    assert not obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2'}})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=False,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    # windows is always str
    expected_cmd = get_plat(['blah', '-blah1', '--blah2'],
                            'blah -blah1 --blah2')

    mock_run.assert_called_once_with(expected_cmd,
                                     cwd=None,
                                     shell=False,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_dict_save_false_shell_true():
    """Dict command with save false and shell true."""
    obj = CmdStep('blahname',
                  Context({'cmd': {
                      'run': 'blah -blah1 --blah2'}}),
                  is_shell=True)

    assert obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2'}})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd=None,
                                    is_shell=True,
                                    is_save=False)]

    with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
        with patch('subprocess.run') as mock_run:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     cwd=None,
                                     shell=True,
                                     check=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_dict_save_false_shell_true_cwd_formatting():
    """Dict command with save false and shell true, cwd formatting."""
    obj = CmdStep('blahname', Context({
        'k1': 'v1',
        'k2': 'v2',
        'cmd': {
            'run': 'blah -blah1 --blah2', 'cwd': '/{k1}/{k2}'}}),
        is_shell=True)

    assert obj.is_shell
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'v1',
                                   'k2': 'v2',
                                   'cmd': {
                                       'run': 'blah -blah1 --blah2',
                                       'cwd': '/{k1}/{k2}'}})

    assert obj.commands == [Command('blah -blah1 --blah2',
                                    cwd='/v1/v2',
                                    is_shell=True,
                                    is_save=False)]

    with patch('subprocess.run') as mock_run:
        with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
            obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string in dir /v1/v2: blah -blah1 --blah2')]

    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     check=True,
                                     cwd='/v1/v2',
                                     shell=True,
                                     stdout=None,
                                     stderr=None)


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_false():
    """Dict command with save false and shell false."""
    context = Context({'cmd': {'run': 'blah -blah1 --blah2',
                               'save': True}})

    obj = CmdStep('blahname', context)

    assert obj.is_shell is False
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2',
                                           'save': True}})
    assert obj.commands == [Command('blah -blah1 --blah2',
                                    is_shell=False,
                                    is_save=True)]

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            'err')
        with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
            with patch_logger(sp_mod_name, logging.ERROR) as mock_logger_error:
                obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]

    mock_logger_error.assert_called_once_with('stderr: err')

    # blah is in a list because shell == false on posix.
    # windows is always str
    expected_cmd = get_plat(['blah', '-blah1', '--blah2'],
                            'blah -blah1 --blah2')

    mock_run.assert_called_once_with(expected_cmd,
                                     capture_output=True,
                                     cwd=None,
                                     encoding=None,
                                     shell=False,
                                     text=True)

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == 'std'
    assert context['cmdOut'].stderr == 'err'


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_true():
    """Dict command with save false and shell true."""
    context = Context({'cmd': {'run': 'blah -blah1 --blah2',
                               'save': True}})

    obj = CmdStep('blahname', context, is_shell=True)

    assert obj.is_shell is True
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2',
                                           'save': True}})

    assert obj.commands == [Command('blah -blah1 --blah2',
                                    is_shell=True,
                                    is_save=True)]

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            None)
        with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
            with patch_logger(sp_mod_name, logging.INFO) as mock_logger_info:
                obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]
    mock_logger_info.assert_called_once_with('stdout: std')

    # blah is in a str because shell == true
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     capture_output=True,
                                     cwd=None,
                                     encoding=None,
                                     shell=True,
                                     text=True)

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == 'std'
    assert context['cmdOut'].stderr is None


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_true_cwd_set():
    """Dict command with save false and shell true with cwd set."""
    context = Context({'cmd': {'run': 'blah -blah1 --blah2',
                               'save': True,
                               'cwd': 'pathhere'}})

    obj = CmdStep('blahname', context, is_shell=True)

    assert obj.is_shell is True
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2',
                                           'save': True,
                                           'cwd': 'pathhere'}})

    assert obj.commands == [Command('blah -blah1 --blah2',
                                    is_shell=True,
                                    cwd='pathhere',
                                    is_save=True)]

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            None)
        with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
            with patch_logger(sp_mod_name, logging.INFO) as mock_logger_info:
                obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string in dir pathhere: blah -blah1 --blah2')]

    mock_logger_info.assert_called_once_with('stdout: std')

    # blah is in a str because shell is true
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     capture_output=True,
                                     cwd='pathhere',
                                     encoding=None,
                                     shell=True,
                                     text=True)

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == 'std'
    assert context['cmdOut'].stderr is None


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_false_formatting():
    """Dict command with save false and shell false with formatting."""
    context = Context({'k1': 'blah',
                       'k2': True,
                       'cmd': {'run': '{k1} -{k1}1 --{k1}2',
                               'save': '{k2}'}})

    obj = CmdStep('blahname', context)

    assert obj.is_shell is False
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'k2': True,
                                   'cmd': {'run': '{k1} -{k1}1 --{k1}2',
                                           'save': '{k2}'}})

    assert obj.commands == [Command('blah -blah1 --blah2', is_save=True)]

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            'err')
        with patch_logger(sp_mod_name, logging.DEBUG) as mock_logger_debug:
            with patch_logger(sp_mod_name,
                              logging.ERROR) as mock_logger_error:
                obj.run_step()

    assert mock_logger_debug.mock_calls == [
        call('stdout & stderr inheriting from parent process.'),
        call('Processing command string: blah -blah1 --blah2')]
    mock_logger_error.assert_called_once_with('stderr: err')

    # blah is in a list because shell == false on posix.
    # windows is always str
    expected_cmd = get_plat(['blah', '-blah1', '--blah2'],
                            'blah -blah1 --blah2')

    mock_run.assert_called_once_with(expected_cmd,
                                     capture_output=True,
                                     cwd=None,
                                     encoding=None,
                                     shell=False,
                                     text=True)

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == 'std'
    assert context['cmdOut'].stderr == 'err'
