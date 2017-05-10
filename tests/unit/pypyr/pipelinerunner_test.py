"""pipelinerunner.py unit tests."""
import os
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          PyModuleNotFoundError)
import pypyr.pipelinerunner
import pytest
from unittest.mock import call, mock_open, patch

# ------------------------- parser mocks -------------------------------------#


def mock_parser(context_arg):
    """Arbitrary mock function to execute instead of get_parsed_context"""
    return Context({'key1': 'created in mock parser', 'key2': context_arg})


def mock_parser_none(context_arg):
    """Return None, mocking get_parsed_context"""
    return None
# ------------------------- parser mocks -------------------------------------#

# ------------------------- get_parsed_context--------------------------------#


def test_get_parsed_context_no_parser():
    """get_parsed_context returns empty Context when no parser specified."""
    context = pypyr.pipelinerunner.get_parsed_context({}, None)

    assert isinstance(context, Context)
    assert len(context) == 0


def test_get_parsed_context_parser_not_found():
    """get_parsed_context raises if parser module specified but not found."""
    with pytest.raises(PyModuleNotFoundError):
        pypyr.pipelinerunner.get_parsed_context(
            {'context_parser': 'unlikelyblahmodulenameherexxssz'}, None)


@patch('pypyr.moduleloader.get_module')
def test_get_parsed_context_parser_returns_none(mocked_moduleloader):
    """get_parsed_context returns empty Context when parser returns None."""
    mocked_moduleloader.return_value.get_parsed_context = mock_parser_none

    context = pypyr.pipelinerunner.get_parsed_context(
        {'context_parser': 'specifiedparserhere'}, 'in arg here')

    mocked_moduleloader.assert_called_once_with('specifiedparserhere')

    assert isinstance(context, Context)
    assert len(context) == 0


@patch('pypyr.moduleloader.get_module')
def test_get_parsed_context_parser_pass(mocked_moduleloader):
    """get_parsed_context passes arg param and returns context."""
    mocked_moduleloader.return_value.get_parsed_context = mock_parser

    context = pypyr.pipelinerunner.get_parsed_context(
        {'context_parser': 'specifiedparserhere'}, 'in arg here')

    mocked_moduleloader.assert_called_once_with('specifiedparserhere')

    assert isinstance(context, Context)
    assert len(context) == 2
    context['key1'] == 'created in mock parser'
    context['key2'] == 'in arg here'


@patch('pypyr.moduleloader.get_module', return_value=3)
def test_get_parser_context_signature_wrong(mocked_moduleloader):
    """Raise when parser found but no get_parsed_context attr."""
    with pytest.raises(AttributeError) as err_info:
        pypyr.pipelinerunner.get_parsed_context(
            {'context_parser': 'specifiedparserhere'}, 'in arg here')

    assert repr(err_info.value) == (
        "AttributeError(\"'int' object has no attribute "
        "'get_parsed_context'\",)")

# ------------------------- get_parsed_context--------------------------------#

# ------------------------- get_pipeline_definition --------------------------#


@patch('ruamel.yaml.safe_load', return_value='mocked pipeline def')
@patch('pypyr.moduleloader.get_pipeline_path', return_value='arb/path/x.yaml')
def test_get_pipeline_definition_pass(mocked_get_path,
                                      mocked_yaml):
    """get_pipeline_definition passes correct params to all methods."""
    with patch('pypyr.pipelinerunner.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        pipeline_def = pypyr.pipelinerunner.get_pipeline_definition(
            'pipename', '/working/dir')

    assert pipeline_def == 'mocked pipeline def'
    mocked_get_path.assert_called_once_with(
        pipeline_name='pipename', working_directory='/working/dir')
    mocked_open.assert_called_once_with('arb/path/x.yaml')
    mocked_yaml.assert_called_once_with(mocked_open.return_value)


@patch('pypyr.moduleloader.get_pipeline_path', return_value='arb/path/x.yaml')
def test_get_pipeline_definition_file_not_found(mocked_get_path):
    """get_pipeline_definition raises file not found."""
    with patch('pypyr.pipelinerunner.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        mocked_open.side_effect = FileNotFoundError('deliberate err')
        with pytest.raises(FileNotFoundError):
            pypyr.pipelinerunner.get_pipeline_definition(
                'pipename', '/working/dir')

# ------------------------- get_pipeline_definition --------------------------#

# ------------------------- main ---------------------------------------------#


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value='parsed context')
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_get_main_pass(mocked_work_dir,
                       mocked_get_pipe_def,
                       mocked_get_parsed_context,
                       mocked_run_step_group):
    """main passes correct params to all methods"""

    pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                              pipeline_context_input='arb context input',
                              working_dir='arb/dir',
                              log_level=77)

    mocked_work_dir.assert_called_once_with('arb/dir')
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # 1st called steps, then on_success
    expected_run_step_groups = [call(context='parsed context',
                                     pipeline_definition='pipe def',
                                     step_group_name='steps'),
                                call(context='parsed context',
                                     pipeline_definition='pipe def',
                                     step_group_name='on_success')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value='parsed context')
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_get_main_parse_context_error(mocked_work_dir,
                                      mocked_get_pipe_def,
                                      mocked_get_parsed_context,
                                      mocked_run_step_group):
    """main runs on_failure with {} dict if context parse fails."""
    mocked_get_parsed_context.side_effect = ContextError

    with pytest.raises(ContextError):
        pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                                  pipeline_context_input='arb context input',
                                  working_dir='arb/dir',
                                  log_level=77)

    mocked_work_dir.assert_called_once_with('arb/dir')
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # No called steps, just on_failure since err on parse context already
    expected_run_step_groups = [call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='on_failure')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value='parsed context')
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_get_main_steps_error(mocked_work_dir,
                              mocked_get_pipe_def,
                              mocked_get_parsed_context,
                              mocked_run_step_group):
    """main runs on_failure if steps group fails."""
    # First time it runs is steps - give a KeyNotInContextError. After that it
    # runs again to process the failure condition - thus None.
    mocked_run_step_group.side_effect = [KeyNotInContextError, None]

    with pytest.raises(KeyNotInContextError):
        pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                                  pipeline_context_input='arb context input',
                                  working_dir='arb/dir',
                                  log_level=77)

    mocked_work_dir.assert_called_once_with('arb/dir')
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # 1st called steps, then on_success
    expected_run_step_groups = [call(context='parsed context',
                                     pipeline_definition='pipe def',
                                     step_group_name='steps'),
                                call(context='parsed context',
                                     pipeline_definition='pipe def',
                                     step_group_name='on_failure')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)

# ------------------------- main----------------------------------------------#

# ------------------------- integration---------------------------------------#


def test_pipeline_runner_main():
    """Smoke test for pipeline runner main.

    Strictly speaking this is an integration test, not a unit test.
    """
    working_dir = os.path.join(
        os.getcwd(),
        'tests')
    pypyr.pipelinerunner.main(pipeline_name='smoke',
                              pipeline_context_input=None,
                              working_dir=working_dir,
                              log_level=50)
# ------------------------- integration---------------------------------------#
