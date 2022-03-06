"""pipeline.py unit tests.

A lot of the tests for the Pipeline.new_pipe_and_args factory constructor
exist in ./pipelinerunner_test.py, which tests at a higher level that the
inputs from a run request map as expected into the Pipeline instance.
"""
import logging
from unittest.mock import call, patch, Mock

import pytest

from pypyr.cache.loadercache import loader_cache
from pypyr.cache.parsercache import contextparser_cache
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          PyModuleNotFoundError,
                          Stop,
                          StopPipeline,
                          StopStepGroup)
from pypyr.pipeline import Pipeline
from pypyr.pipedef import PipelineDefinition, PipelineInfo
from tests.common.utils import DeepCopyMagicMock

from tests.common.utils import patch_logger


def get_pipe_def(dict_in, info=None):
    """Wrap input dict & info into a PipelineDefinition."""
    return PipelineDefinition(pipeline=dict_in, info=info)

# region context parser
# region parser mocks


def mock_parser_arb(args):
    """Arbitrary mock function to execute instead of get_parsed_context."""
    return Context({'key1': 'created in mock parser', 'key2': args})


def mock_parser_none(args):
    """Return None, mocking get_parsed_context."""
    return None
# endregion parser mocks


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_get_parsed_context_no_parser(mock_get_pipeline):
    """On get_parsed_context return empty Context when no parser specified."""
    mock_get_pipeline.return_value = get_pipe_def({})
    context = Context()
    pipeline = Pipeline('arb')
    pipeline.run(context)

    assert context == {}
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_get_parsed_context_parser_not_found(mock_get_pipeline):
    """On get_parsed_context raise if parser module specified but not found."""
    mock_get_pipeline.return_value = get_pipe_def({
        'context_parser': 'unlikelyblahmodulenameherexxssz'})
    context = Context()
    pipeline = Pipeline('arb')

    with pytest.raises(PyModuleNotFoundError):
        pipeline.run(context)

    assert context == {}
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)


@patch('pypyr.moduleloader.get_module')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_get_parsed_context_parser_returns_none(mock_get_pipeline,
                                                mock_moduleloader):
    """On get_parsed_context return empty Context when parser returns None."""
    mock_moduleloader.return_value.get_parsed_context = mock_parser_none
    mock_get_pipeline.return_value = get_pipe_def(
        {'context_parser': 'specifiedparserhere'})

    pipeline = Pipeline('arb', context_args=['in arg here'])

    context = Context()

    pipeline.run(context)

    mock_moduleloader.assert_called_once_with('specifiedparserhere')
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)
    assert context == {}


@patch('pypyr.moduleloader.get_module')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_get_parsed_context_parser_pass(mock_get_pipeline, mock_moduleloader):
    """On get_parsed_context pass arg param and returns context."""
    contextparser_cache.clear()
    mock_moduleloader.return_value.get_parsed_context = mock_parser_arb
    mock_get_pipeline.return_value = get_pipe_def(
        {'context_parser': 'specifiedparserhere'})

    pipeline = Pipeline('arb', context_args='in arg here')

    context = Context()

    pipeline.run(context)

    mock_moduleloader.assert_called_once_with('specifiedparserhere')
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)

    assert isinstance(context, Context)
    assert len(context) == 2
    assert context['key1'] == 'created in mock parser'
    assert context['key2'] == 'in arg here'


@patch('pypyr.moduleloader.get_module', return_value=3)
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_get_parser_context_signature_wrong(mock_get_pipeline,
                                            mock_moduleloader):
    """Raise when parser found but no get_parsed_context attr."""
    contextparser_cache.clear()

    mock_get_pipeline.return_value = get_pipe_def(
        {'context_parser': 'specifiedparserhere'})

    pipeline = Pipeline('arb', context_args='in arg here')

    context = Context()

    with pytest.raises(AttributeError) as err_info:
        pipeline.run(context)

    mock_moduleloader.assert_called_once_with('specifiedparserhere')
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)

    assert str(err_info.value) == ("'int' object has no attribute "
                                   "'get_parsed_context'")


@patch('pypyr.moduleloader.get_module')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_prepare_context_empty_parse(mock_get_pipeline,
                                     mock_moduleloader):
    """Empty parsed_context works."""
    contextparser_cache.clear()
    parser = Mock()
    parser.return_value = {}
    mock_moduleloader.return_value.get_parsed_context = parser
    mock_get_pipeline.return_value = get_pipe_def(
        {'context_parser': 'specifiedparserhere'})

    pipeline = Pipeline('arb', context_args='arb context input')

    context = Context({'c1': 'cv1', 'c2': 'cv2'})

    pipeline.run(context)

    mock_moduleloader.assert_called_once_with('specifiedparserhere')
    parser.assert_called_once_with('arb context input')
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)

    assert context == {'c1': 'cv1', 'c2': 'cv2'}


@patch('pypyr.moduleloader.get_module')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
def test_prepare_context_with_parse_merge(mock_get_pipeline,
                                          mock_moduleloader):
    """On parsed_context override context."""
    contextparser_cache.clear()
    parser = Mock()
    parser.return_value = {'a': 'av1', 'c1': 'new value from parsed'}
    mock_moduleloader.return_value.get_parsed_context = parser
    mock_get_pipeline.return_value = get_pipe_def(
        {'context_parser': 'specifiedparserhere'})

    pipeline = Pipeline('arb', context_args='arb context input')

    context = Context({'c1': 'cv1', 'c2': 'cv2'})
    pipeline.run(context)

    mock_moduleloader.assert_called_once_with('specifiedparserhere')
    parser.assert_called_once_with('arb context input')
    mock_get_pipeline.assert_called_once_with(name='arb', parent=None)

    assert context == {'a': 'av1', 'c1': 'new value from parsed', 'c2': 'cv2'}

# endregion context parser

# region loader


def test_arbitrary_loader_module_not_found():
    """Raise when loader not found."""
    loader_cache.clear()

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        loader='not_found_loader')

    with pytest.raises(PyModuleNotFoundError):
        pipeline.run(Context())


def test_loader_no_get_pipeline_definition():
    """Arbitrary loader module without `get_pipeline_definition` function."""
    loader_cache.clear()
    import sys
    current_module = sys.modules[__name__]

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        loader=__name__)
    with patch_logger(
            'pypyr.cache.loadercache',
            logging.ERROR) as mock_logger_error:
        with pytest.raises(AttributeError) as err:
            pipeline.run(Context())

    assert str(err.value) == f"module '{__name__}' " \
        "has no attribute 'get_pipeline_definition'"

    mock_logger_error.assert_called_once_with(
        f"The pipeline loader {current_module} doesn't have a "
        "get_pipeline_definition(pipeline_name, parent) function."
    )


@patch('pypyr.loaders.file.get_pipeline_definition')
def test_empty_loader_set_up_to_default(mock_get_pipeline_definition):
    """Default loader should be pypyr.loaders.file."""
    loader_cache.clear()

    mock_get_pipeline_definition.return_value = get_pipe_def({'steps': None})

    pipeline = Pipeline('arb pipe', context_args='arb context input')
    pipeline.run(Context())

    mock_get_pipeline_definition.assert_called_once_with(
        pipeline_name='arb pipe',
        parent=None
    )


@patch('pypyr.loaders.file.get_pipeline_definition')
def test_empty_loader_set_up_to_default_with_parent(
        mock_get_pipeline_definition):
    """Default loader should be pypyr.loaders.file with parent."""
    loader_cache.clear()

    mock_get_pipeline_definition.return_value = get_pipe_def({'steps': None})

    pipeline = Pipeline('arb pipe', context_args='arb context input')
    pipeline.load_and_run_pipeline(Context(), parent='/arb/dir')

    mock_get_pipeline_definition.assert_called_once_with(
        pipeline_name='arb pipe',
        parent='/arb/dir'
    )


def test_arb_loader():
    """Test loader set up."""
    loader_cache.clear()

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        loader='arbpack.arbloader',
                        py_dir='tests')
    pipeline.load_and_run_pipeline(Context(), parent='/arb/dir')

    loader = loader_cache.get_pype_loader('arbpack.arbloader')
    assert loader.name == 'arbpack.arbloader'
    assert loader.get_pipeline('arb pipe', '/arb/dir').pipeline == {
        'pipeline_name': 'arb pipe', 'parent': '/arb/dir'}

    loader_cache.clear()


def test_arb_loader_no_parent():
    """Test loader set up with no parent."""
    loader_cache.clear()

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        loader='arbpack.arbloader',
                        py_dir='tests')
    pipeline.load_and_run_pipeline(Context())

    loader = loader_cache.get_pype_loader('arbpack.arbloader')
    assert loader.name == 'arbpack.arbloader'
    assert loader.get_pipeline('arb pipe', None).pipeline == {
        'pipeline_name': 'arb pipe', 'parent': None}

    loader_cache.clear()

# endregion loader

# region run_pipeline


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_pass_minimal(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Create implicit context if doesn't exist & no context parser."""
    pipe_def = get_pipe_def({'arb': 'pipe'})
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'a': 'b'}
    mock_parser.return_value = parser

    pipeline = Pipeline('arb pipe', context_args='arb context input')
    context_instance = Context()
    with patch('pypyr.pipeline.Context') as mock_context:
        mock_context.return_value = context_instance
        pipeline.load_and_run_pipeline(None)

    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_not_called()
    parser.assert_not_called()

    mock_context.assert_called_once()

    # assure that stack empty when done
    assert not context_instance._stack

    mock_steps_runner.assert_called_once_with(
        pipeline_body={'arb': 'pipe'},
        context=context_instance)
    # No called steps
    sr = mock_steps_runner.return_value
    sr.run_step_groups.assert_called_once_with(groups=['steps'],
                                               success_group='on_success',
                                               failure_group='on_failure')
    sr.run_failure_step_group.assert_not_called()


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_pass_skip_parse_context(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Explicit False parse_input doesn't run parser."""
    pipe_def = get_pipe_def({'arb': 'pipe'})
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'a': 'b'}
    mock_parser.return_value = parser

    context = Context({'c': 'd'})
    pipeline = Pipeline('arb pipe', parse_input=False)
    pipeline.load_and_run_pipeline(context)

    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)
    mock_parser.assert_not_called()
    parser.assert_not_called()

    mock_steps_runner.assert_called_once_with(
        pipeline_body={'arb': 'pipe'},
        context=context)
    # No called steps, just on_failure since err on parse context already
    sr = mock_steps_runner.return_value
    sr.run_step_groups.assert_called_once_with(groups=['steps'],
                                               success_group='on_success',
                                               failure_group='on_failure')
    sr.run_failure_step_group.assert_not_called()


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_parse_context_error(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """run_pipeline on_failure with Context as is if parse fails."""
    pipe_def = get_pipe_def({'context_parser': 'arb parser'})
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.side_effect = ContextError
    mock_parser.return_value = parser

    context = Context({'c': 'd'})
    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        parse_input=True)

    with pytest.raises(ContextError):
        pipeline.load_and_run_pipeline(context)

    assert context == {'c': 'd'}
    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.assert_called_once_with(
        pipeline_body=pipe_def.pipeline,
        context=context)
    # No called steps, just on_failure since err on parse context already
    sr = mock_steps_runner.return_value
    sr.run_step_groups.assert_not_called()
    sr.run_failure_step_group.assert_called_once_with('on_failure')


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_steps_error_raises(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run on_failure and raise error if steps group fails."""
    # First time it runs is steps - give a KeyNotInContextError.
    pipe_def = get_pipe_def({'context_parser': 'arb parser'})
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'a': 'b'}
    mock_parser.return_value = parser

    context = Context({'c': 'd'})
    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        parse_input=True)

    mock_steps_runner.return_value.run_step_groups.side_effect = (
        KeyNotInContextError)

    with pytest.raises(KeyNotInContextError):
        pipeline.run(context)

    assert context == {'a': 'b', 'c': 'd'}

    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='on_success',
        failure_group='on_failure'
    )
    mock_steps_runner.assert_called_once_with(
        pipeline_body=pipe_def.pipeline,
        context=context)


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_existing_context_pass(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Pipeline runs with existing context."""
    pipe_def = get_pipe_def({'context_parser': 'arb parser'})
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input')
    pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='on_success',
        failure_group='on_failure'
    )
    mock_steps_runner.assert_called_once_with(
        pipeline_body={'context_parser': 'arb parser'},
        context={'1': 'context 1',
                 '2': 'context2',
                 '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_dir_specified(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Py dir passed to add_sys_path."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        py_dir='/arb/dir')
    pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_called_once_with('/arb/dir')
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='on_success',
        failure_group='on_failure'
    )
    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'1': 'context 1',
                                                       '2': 'context2',
                                                       '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_group_specified(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run pipeline with specified groups."""
    pipe_yaml = {'arb': 'pipe'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        groups=['arb1', 'arb2'])

    pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_not_called()
    parser.assert_not_called()

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['arb1', 'arb2'],
        success_group=None,
        failure_group=None
    )
    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'2': 'original',
                                                       '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_parent_specified(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run pipeline with specified parent."""
    pipe_yaml = {'arb': 'pipe'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe')

    pipeline.load_and_run_pipeline(context, '/parent')

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()
    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent='/parent')

    mock_parser.assert_not_called()
    parser.assert_not_called()

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='on_success',
        failure_group='on_failure'
    )
    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'2': 'original',
                                                       '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_success_group_specified(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run pipeline with specified success group."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        success_group='arb1')

    pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()

    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='arb1',
        failure_group=None
    )
    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'1': 'context 1',
                                                       '2': 'context2',
                                                       '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_failure_group_specified(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run pipeline with specified failure group."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        failure_group='arb1')

    pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()

    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group=None,
        failure_group='arb1'
    )
    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'1': 'context 1',
                                                       '2': 'context2',
                                                       '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_load_and_run_pipeline_with_group_and_failure_group_specified(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Pass run_pipeline with specified group and failure group."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.return_value = {'1': 'context 1', '2': 'context2'}
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        groups=['arb1'],
                        failure_group='arb2')

    pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_get_pipe.assert_called_once_with(name='arb pipe',
                                          parent=None)

    mock_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['arb1'],
        success_group=None,
        failure_group='arb2'
    )
    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'1': 'context 1',
                                                       '2': 'context2',
                                                       '3': 'new'})


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_run_pipeline_parse_context_error_failure(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run on_failure on context parse exception."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.side_effect = ValueError('arb')
    mock_parser.return_value = parser

    context = Context({'2': 'original', '3': 'new'})

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input',
                        groups=['gr'],
                        success_group='sg',
                        failure_group='fg')

    with pytest.raises(ValueError) as err:
        pipeline.run(context)

    assert str(err.value) == 'arb'

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={'2': 'original',
                                                       '3': 'new'})
    # No called steps, just on_failure since err on parse context already
    sr = mock_steps_runner.return_value
    sr.run_step_groups.assert_not_called()
    sr.run_failure_step_group.assert_called_once_with('fg')


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_run_pipeline_parse_context_error_failure_stop(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Run on_failure on context parser exception with Stop."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.side_effect = ValueError('arb')
    mock_parser.return_value = parser

    sr = mock_steps_runner.return_value

    sr.run_failure_step_group.side_effect = Stop()

    context = Context()
    pipeline = Pipeline('arb pipe',
                        context_args='arb context input')

    with pytest.raises(Stop):
        pipeline.load_and_run_pipeline(context)

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={})

    # No called steps, just on_failure since err on parse context already
    sr.run_step_groups.assert_not_called()
    sr.run_failure_step_group.assert_called_once_with('on_failure')


@patch('pypyr.pipeline.StepsRunner', autospec=True)
@patch('pypyr.cache.parsercache.contextparser_cache.get_context_parser')
@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.moduleloader.add_sys_path')
def test_run_pipeline_parse_context_error_failure_stopstepgroup(
        mock_add_sys_path,
        mock_get_pipe,
        mock_parser,
        mock_steps_runner):
    """Context failure handler swallows StopStepGroup."""
    pipe_yaml = {'context_parser': 'arb parser'}
    pipe_def = get_pipe_def(pipe_yaml)
    mock_get_pipe.return_value = pipe_def

    parser = Mock()
    parser.side_effect = ValueError('arb')
    mock_parser.return_value = parser

    sr = mock_steps_runner.return_value

    sr.run_failure_step_group.side_effect = StopStepGroup()
    context = Context()

    pipeline = Pipeline('arb pipe',
                        context_args='arb context input')

    with pytest.raises(ValueError) as err:
        pipeline.load_and_run_pipeline(context)

    assert str(err.value) == 'arb'

    assert not context.is_in_pipeline_scope
    mock_add_sys_path.assert_not_called()

    mock_parser.assert_called_once_with('arb parser')
    parser.assert_called_once_with('arb context input')

    mock_steps_runner.assert_called_once_with(pipeline_body=pipe_yaml,
                                              context={})

    # No called steps, just on_failure since err on parse context already
    sr.run_step_groups.assert_not_called()
    sr.run_failure_step_group.assert_called_once_with('on_failure')

# endregion run_pipeline

# region Stop & StopPipeline

# region stop helpers


def get_test_pipeline_definition(pipeline):
    """Wrap input pipeline (dict) into a PipelineDefinition.

    Args:
        pipeline (dict-like): pipeline payload.

    Returns:
        PipelineDefinition with pipeline payload and arb PipelineInfo.
    """
    return PipelineDefinition(
        pipeline=pipeline,
        info=PipelineInfo(pipeline_name='arbpipe',
                          loader='arbloader',
                          parent='arbdir'))


def get_step_pipeline():
    """Test pipeline for jump wrapped in PipelineDefinition."""
    return get_test_pipeline_definition(get_step_pipeline_payload())


def get_step_pipeline_payload():
    """Bare dict pipeline payload."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


def nothing_step(context):
    """Mock step."""
    pass


def stop_pipe_step(context):
    """Mock stop pipeline step."""
    raise StopPipeline()


def stop_all_step(context):
    """Mock stop all step."""
    raise Stop()

# endregion stop helpers


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_pipeline(mock_step_cache, mock_get_pipe):
    """When StopPipeline stop pipeline execution."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 (StopPipeline)
    mock_step_cache.side_effect = [
        nothing_step,  # 2.1
        nothing_step,  # 2.2
        stop_pipe_step,  # 3.1
    ]

    mock_get_pipe.return_value = get_test_pipeline_definition(
        get_step_pipeline_payload())
    context = Context()

    pipeline = Pipeline('arb pipe',
                        groups=['sg2', 'sg3', 'sg4', 'sg1'],
                        success_group='sg5',
                        failure_group=None)

    pipeline.run(context)

    assert not context.is_in_pipeline_scope
    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_pipeline_for(mock_step_cache, mock_get_pipe):
    """When StopPipeline stop pipeline execution in for loop."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 x2 (StopPipeline)

    nothing_mock = DeepCopyMagicMock()
    mock312 = DeepCopyMagicMock()

    def step31(context):
        mock312(context)
        if context['i'] == 'two':
            raise StopPipeline()

    mock_step_cache.side_effect = [
        nothing_mock,  # 2.1
        nothing_mock,  # 2.2
        step31,  # 3.1
    ]

    mock_get_pipe.return_value = get_for_step_pipeline()
    context = Context()

    pipeline = Pipeline('arb pipe',
                        groups=['sg2', 'sg3', 'sg4', 'sg1'],
                        success_group='sg5',
                        failure_group=None)

    pipeline.run(context)

    assert not context.is_in_pipeline_scope
    assert nothing_mock.mock_calls == [call({}),
                                       call({})
                                       ]

    assert mock312.mock_calls == [call({'i': 'one'}),
                                  call({'i': 'two'})]

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


def get_retry_step_pipeline():
    """Test pipeline for retry loop."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            {'name': 'sg3.step1',
             'retry': {'max': 3}
             },
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_pipeline_retry(mock_step_cache, mock_get_pipe):
    """When StopPipeline stop pipeline execution in retry loop."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 x2 (StopPipeline)

    nothing_mock = DeepCopyMagicMock()
    mock312 = DeepCopyMagicMock()

    def step31(context):
        mock312(context)
        if context['retryCounter'] == 2:
            raise StopPipeline()
        else:
            raise ValueError(context['retryCounter'])

    mock_step_cache.side_effect = [
        nothing_mock,  # 2.1
        nothing_mock,  # 2.2
        step31,  # 3.1
    ]

    pipe_yaml = get_retry_step_pipeline()
    mock_get_pipe.return_value = get_test_pipeline_definition(pipe_yaml)
    context = Context()

    pipeline = Pipeline('arb pipe',
                        groups=['sg2', 'sg3', 'sg4', 'sg1'],
                        success_group='sg5',
                        failure_group=None)

    pipeline.run(context)

    assert not context.is_in_pipeline_scope

    assert nothing_mock.mock_calls == [call({}),
                                       call({})
                                       ]

    assert mock312.mock_calls == [call({'retryCounter': 1}),
                                  call({'retryCounter': 2})]

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_all(mock_step_cache, mock_get_pipe):
    """Stop stops pipeline execution."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 (StopPipeline)
    mock_step_cache.side_effect = [
        nothing_step,  # 2.1
        nothing_step,  # 2.2
        stop_all_step,  # 3.1
    ]

    mock_get_pipe.return_value = get_step_pipeline()

    context = Context()

    pipeline = Pipeline('arb pipe',
                        groups=['sg2', 'sg3', 'sg4', 'sg1'],
                        success_group='sg5',
                        failure_group=None)

    pipeline.run(context)

    assert not context.is_in_pipeline_scope

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


def get_while_step_pipeline():
    """Test pipeline for while."""
    return get_test_pipeline_definition({
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            {'name': 'sg3.step1',
             'while': {
                 'max': 3},
             },
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    })


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_all_while(mock_step_cache, mock_get_pipe):
    """Stop stops pipeline execution inside a while."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 loop 3, StopPipeline on 2
    nothing_mock = DeepCopyMagicMock()
    mock312 = DeepCopyMagicMock()

    def step31(context):
        mock312(context)
        if context['whileCounter'] == 2:
            raise Stop()

    mock_step_cache.side_effect = [
        nothing_mock,  # 2.1
        nothing_mock,  # 2.2
        step31  # 3.1.2
    ]
    mock_get_pipe.return_value = get_while_step_pipeline()

    context = Context()

    pipeline = Pipeline('arb pipe',
                        groups=['sg2', 'sg3', 'sg4', 'sg1'],
                        success_group='sg5',
                        failure_group=None)

    pipeline.run(context)

    assert not context.is_in_pipeline_scope

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]

    assert nothing_mock.mock_calls == [call({}),
                                       call({})
                                       ]

    assert mock312.mock_calls == [call({'whileCounter': 1}),
                                  call({'whileCounter': 2})]


def get_for_step_pipeline():
    """Test pipeline for for loop."""
    return get_test_pipeline_definition(get_for_step_pipeline_payload())


def get_for_step_pipeline_payload():
    """Bare dict for for pipeline."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            {'name': 'sg3.step1',
             'foreach': ['one', 'two', 'three']
             },
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.loadercache.Loader.get_pipeline')
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_all_for(mock_step_cache, mock_get_pipe):
    """Stop stops pipeline execution inside a for loop."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 loop 3, StopPipeline on 2
    nothing_mock = DeepCopyMagicMock()
    mock312 = DeepCopyMagicMock()

    def step31(context):
        mock312(context)
        if context['i'] == 'two':
            raise Stop()

    mock_step_cache.side_effect = [
        nothing_mock,  # 2.1
        nothing_mock,  # 2.2
        step31  # 3.1.2
    ]

    mock_get_pipe.return_value = get_for_step_pipeline()

    context = Context()

    pipeline = Pipeline('arb pipe',
                        groups=['sg2', 'sg3', 'sg4', 'sg1'],
                        success_group='sg5',
                        failure_group=None)

    pipeline.run(context)

    assert not context.is_in_pipeline_scope

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]

    assert nothing_mock.mock_calls == [call({}),
                                       call({})
                                       ]

    assert mock312.mock_calls == [call({'i': 'one'}),
                                  call({'i': 'two'})]
# endregion Stop & StopPipeline
