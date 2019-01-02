"""cmd.py unit tests."""
import logging
import pytest
import subprocess
from unittest.mock import patch
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.steps.dsl.cmd import CmdStep

# ------------------------- FileInRewriterStep -------------------------------


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
        "blah cmd config should be either a simple string cmd='mycommandhere' "
        "or a dictionary cmd={'run': 'mycommandhere', 'save': False}.")


def test_cmdstep_cmd_is_string():
    """Str command is always not is_save."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': 'blah'}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah'})
    assert obj.cmd_text == 'blah'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah')


def test_cmdstep_cmd_is_dict_default_save_false():
    """Dict command defaults not is_save."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': {'run': 'blah'}}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah'}})
    assert obj.cmd_text == 'blah'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah')


def test_cmdstep_cmd_is_dict_default_save_true():
    """Dict command with is_save true."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': {'run': 'blah',
                                                   'save': True}}))

    assert obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah', 'save': True}})
    assert obj.cmd_text == 'blah'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah')


def test_cmdstep_runstep_cmd_is_string_shell_false():
    """Str command is always not is_save."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': 'blah -blah1 --blah2'}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah -blah1 --blah2'})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah -blah1 --blah2')

    with patch('subprocess.run') as mock_run:
        obj.run_step(is_shell=False)

    # blah is in a list because shell == false
    mock_run.assert_called_once_with(['blah', '-blah1', '--blah2'],
                                     shell=False, check=True)


def test_cmdstep_runstep_cmd_is_string_formatting_shell_false():
    """Str command is always not is_save and works with formatting."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'k1': 'blah',
                                           'cmd': '{k1} -{k1}1 --{k1}2'}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'cmd': '{k1} -{k1}1 --{k1}2'})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: {k1} -{k1}1 --{k1}2')

    with patch('subprocess.run') as mock_run:
        obj.run_step(is_shell=False)

    # blah is in a list because shell == false
    mock_run.assert_called_once_with(['blah', '-blah1', '--blah2'],
                                     shell=False, check=True)


def test_cmdstep_runstep_cmd_is_string_shell_true():
    """Str command is always not is_save."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': 'blah -blah1 --blah2'}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': 'blah -blah1 --blah2'})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah -blah1 --blah2')

    with patch('subprocess.run') as mock_run:
        obj.run_step(is_shell=True)

    # blah is in a list because shell == false
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     shell=True, check=True)


def test_cmdstep_runstep_cmd_is_string_formatting_shell_true():
    """Str command is always not is_save and works with formatting."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'k1': 'blah',
                                           'cmd': '{k1} -{k1}1 --{k1}2'}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'cmd': '{k1} -{k1}1 --{k1}2'})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: {k1} -{k1}1 --{k1}2')

    with patch('subprocess.run') as mock_run:
        obj.run_step(is_shell=True)

    # blah is a string because shell == true
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     shell=True, check=True)


def test_cmdstep_runstep_cmd_is_dict_save_false_shell_false():
    """Dict command with save false and shell false."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': {
            'run': 'blah -blah1 --blah2'}}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2'}})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah -blah1 --blah2')

    with patch('subprocess.run') as mock_run:
        obj.run_step(is_shell=False)

    # blah is in a list because shell == false
    mock_run.assert_called_once_with(['blah', '-blah1', '--blah2'],
                                     shell=False, check=True)


def test_cmdstep_runstep_cmd_is_dict_save_false_shell_true():
    """Dict command with save false and shell true."""
    logger = logging.getLogger('blahname')
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', Context({'cmd': {
            'run': 'blah -blah1 --blah2'}}))

    assert not obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2'}})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah -blah1 --blah2')

    with patch('subprocess.run') as mock_run:
        obj.run_step(is_shell=True)

    # blah is in a list because shell == false
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     shell=True, check=True)


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_false():
    """Dict command with save false and shell false."""
    logger = logging.getLogger('blahname')
    context = Context({'cmd': {'run': 'blah -blah1 --blah2',
                               'save': True}})
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', context)

    assert obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2',
                                           'save': True}})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah -blah1 --blah2')

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            'err')
        with patch.object(logger, 'error') as mock_logger_error:
            obj.run_step(is_shell=False)

    mock_logger_error.assert_called_once_with('stderr: err')

    # blah is in a list because shell == false
    mock_run.assert_called_once_with(['blah', '-blah1', '--blah2'],
                                     shell=False,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     # text=True
                                     universal_newlines=True)

    assert context['cmdOut']['returncode'] == 0
    assert context['cmdOut']['stdout'] == 'std'
    assert context['cmdOut']['stderr'] == 'err'


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_true():
    """Dict command with save false and shell true."""
    logger = logging.getLogger('blahname')
    context = Context({'cmd': {'run': 'blah -blah1 --blah2',
                               'save': True}})
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', context)

    assert obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'cmd': {'run': 'blah -blah1 --blah2',
                                           'save': True}})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: blah -blah1 --blah2')

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            None)
        with patch.object(logger, 'info') as mock_logger_info:
            obj.run_step(is_shell=True)

    mock_logger_info.assert_called_once_with('stdout: std')

    # blah is in a list because shell == false
    mock_run.assert_called_once_with('blah -blah1 --blah2',
                                     shell=True,
                                     # capture_output=True,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     # text=True,
                                     universal_newlines=True)

    assert context['cmdOut']['returncode'] == 0
    assert context['cmdOut']['stdout'] == 'std'
    assert context['cmdOut']['stderr'] is None


def test_cmdstep_runstep_cmd_is_dict_save_true_shell_false_formatting():
    """Dict command with save false and shell false with formatting."""
    logger = logging.getLogger('blahname')
    context = Context({'k1': 'blah',
                       'k2': True,
                       'cmd': {'run': '{k1} -{k1}1 --{k1}2',
                               'save': '{k2}'}})
    with patch.object(logger, 'debug') as mock_logger_debug:
        obj = CmdStep('blahname', context)

    assert obj.is_save
    assert obj.logger.name == 'blahname'
    assert obj.context == Context({'k1': 'blah',
                                   'k2': True,
                                   'cmd': {'run': '{k1} -{k1}1 --{k1}2',
                                           'save': '{k2}'}})
    assert obj.cmd_text == 'blah -blah1 --blah2'
    mock_logger_debug.assert_called_once_with(
        'Processing command string: {k1} -{k1}1 --{k1}2')

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(None,
                                                            0,
                                                            'std',
                                                            'err')
        with patch.object(logger, 'error') as mock_logger_error:
            obj.run_step(is_shell=False)

    mock_logger_error.assert_called_once_with('stderr: err')

    # blah is in a list because shell == false
    mock_run.assert_called_once_with(['blah', '-blah1', '--blah2'],
                                     shell=False,
                                     # capture_output=True,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     # text=True,
                                     universal_newlines=True)

    assert context['cmdOut']['returncode'] == 0
    assert context['cmdOut']['stdout'] == 'std'
    assert context['cmdOut']['stderr'] == 'err'
