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


@patch('ruamel.yaml.YAML.load', return_value='mocked pipeline def')
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


@patch('pypyr.pipelinerunner.run_pipeline')
@patch('pypyr.moduleloader.set_working_directory')
def test_main_pass(mocked_work_dir, mocked_run_pipeline):
    """main initializes and runs pipelines."""
    pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                              pipeline_context_input='arb context input',
                              working_dir='arb/dir',
                              log_level=77,
                              log_path=None)

    mocked_work_dir.assert_called_once_with('arb/dir')
    mocked_run_pipeline.assert_called_once_with(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        working_dir='arb/dir')


@patch('pypyr.pipelinerunner.run_pipeline', side_effect=ContextError('arb'))
@patch('pypyr.moduleloader.set_working_directory')
def test_main_fail(mocked_work_dir, mocked_run_pipeline):
    """main raises unhandled error on pipeline failure."""

    with pytest.raises(ContextError) as err_info:
        pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                                  pipeline_context_input='arb context input',
                                  working_dir='arb/dir',
                                  log_level=77,
                                  log_path=None)

    assert repr(err_info.value) == (
        "ContextError('arb',)")

    mocked_work_dir.assert_called_once_with('arb/dir')
    mocked_run_pipeline.assert_called_once_with(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        working_dir='arb/dir')

# ------------------------- main ---------------------------------------------#

# ------------------------- prepare_context - --------------------------------#


@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context())
def test_prepare_context_empty_parse(mocked_get_parsed_context):
    """Empty parsed_context works."""
    context = Context({'c1': 'cv1', 'c2': 'cv2'})
    pypyr.pipelinerunner.prepare_context(pipeline='pipe def',
                                         context_in_string='arb context input',
                                         context=context)

    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    assert context == {'c1': 'cv1', 'c2': 'cv2'}


@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'a': 'av1', 'c1': 'new value from parsed'}))
def test_prepare_context_with_parse_merge(mocked_get_parsed_context):
    """parsed_context overrides context."""
    context = Context({'c1': 'cv1', 'c2': 'cv2'})
    pypyr.pipelinerunner.prepare_context(pipeline='pipe def',
                                         context_in_string='arb context input',
                                         context=context)

    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    assert context == {'a': 'av1', 'c1': 'new value from parsed', 'c2': 'cv2'}
# ------------------------- prepare_context - --------------------------------#

# ------------------------- run_pipeline -------------------------------------#


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context())
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_run_pipeline_pass(mocked_work_dir,
                           mocked_get_pipe_def,
                           mocked_get_parsed_context,
                           mocked_run_step_group):
    """run_pipeline passes correct params to all methods."""

    with patch('pypyr.context.Context') as mock_context:
        mock_context.return_value = Context()
        pypyr.pipelinerunner.run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input',
            working_dir='arb/dir')

    mocked_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # assure that freshly created context instance does have working dir set
    assert mock_context.return_value.working_dir == 'arb/dir'

    # 1st called steps, then on_success
    expected_run_step_groups = [call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='steps'),
                                call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='on_success')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context())
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_run_pipeline_pass_skip_parse_context(mocked_work_dir,
                                              mocked_get_pipe_def,
                                              mocked_get_parsed_context,
                                              mocked_run_step_group):
    """run_pipeline passes correct params to all methods."""

    pypyr.pipelinerunner.run_pipeline(
        pipeline_name='arb pipe',
        working_dir='arb/dir',
        parse_input=False)

    mocked_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_not_called()

    # 1st called steps, then on_success
    expected_run_step_groups = [call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='steps'),
                                call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='on_success')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context')
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_run_pipeline_parse_context_error(mocked_work_dir,
                                          mocked_get_pipe_def,
                                          mocked_get_parsed_context,
                                          mocked_run_step_group):
    """run_pipeline on_failure with empty Context if context parse fails."""
    mocked_get_parsed_context.side_effect = ContextError

    with pytest.raises(ContextError):
        pypyr.pipelinerunner.run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input',
            working_dir='arb/dir')

    mocked_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # No called steps, just on_failure since err on parse context already
    expected_run_step_groups = [call(context=Context(),
                                     pipeline_definition='pipe def',
                                     step_group_name='on_failure')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)

    call_args_tuple = mocked_run_step_group.call_args
    args, kwargs = call_args_tuple
    assert isinstance(kwargs['context'], Context)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'c1': 'cv1'}))
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_run_pipeline_steps_error(mocked_work_dir,
                                  mocked_get_pipe_def,
                                  mocked_get_parsed_context,
                                  mocked_run_step_group):
    """run_pipeline runs on_failure if steps group fails."""
    # First time it runs is steps - give a KeyNotInContextError. After that it
    # runs again to process the failure condition - thus None.
    mocked_run_step_group.side_effect = [KeyNotInContextError, None]

    with pytest.raises(KeyNotInContextError):
        pypyr.pipelinerunner.run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input',
            working_dir='arb/dir')

    mocked_work_dir.assert_not_called()

    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # 1st called steps, then on_success
    expected_run_step_groups = [call(context={'c1': 'cv1'},
                                     pipeline_definition='pipe def',
                                     step_group_name='steps'),
                                call(context={'c1': 'cv1'},
                                     pipeline_definition='pipe def',
                                     step_group_name='on_failure')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context())
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_run_pipeline_steps_error_no_context(mocked_work_dir,
                                             mocked_get_pipe_def,
                                             mocked_get_parsed_context,
                                             mocked_run_step_group):
    """run_pipeline runs on_failure if steps group fails."""
    # First time it runs is steps - give a KeyNotInContextError. After that it
    # runs again to process the failure condition - thus None.
    mocked_run_step_group.side_effect = [KeyNotInContextError, None]

    with pytest.raises(KeyNotInContextError):
        pypyr.pipelinerunner.run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input',
            working_dir='arb/dir')

    mocked_work_dir.assert_not_called()

    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # 1st called steps, then on_success
    expected_run_step_groups = [call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='steps'),
                                call(context={},
                                     pipeline_definition='pipe def',
                                     step_group_name='on_failure')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)


@patch('pypyr.stepsrunner.run_step_group')
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'1': 'context 1', '2': 'context2'}))
@patch('pypyr.pipelinerunner.get_pipeline_definition', return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
def test_run_pipeline_with_existing_context_pass(mocked_work_dir,
                                                 mocked_get_pipe_def,
                                                 mocked_get_parsed_context,
                                                 mocked_run_step_group):
    """run_pipeline passes correct params to all methods"""

    existing_context = Context({'2': 'original', '3': 'new'})
    existing_context.working_dir = 'from/context'

    pypyr.pipelinerunner.run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        working_dir='arb/dir',
        context=existing_context)

    existing_context.working_dir == 'from/context'
    mocked_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='from/context')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # 1st called steps, then on_success. In both cases with merged context.
    expected_run_step_groups = [call(
        context={'1': 'context 1', '2': 'context2', '3': 'new'},
        pipeline_definition='pipe def',
        step_group_name='steps'),
        call(
        context={'1': 'context 1', '2': 'context2', '3': 'new'},
        pipeline_definition='pipe def',
        step_group_name='on_success')]

    mocked_run_step_group.assert_has_calls(expected_run_step_groups)

# ------------------------- run_pipeline -------------------------------------#

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
                              log_level=50,
                              log_path=None)
# ------------------------- integration---------------------------------------#
