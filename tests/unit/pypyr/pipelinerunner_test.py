"""pipelinerunner.py unit tests."""
import logging
import pytest
from unittest.mock import call, patch
from pypyr.cache.loadercache import pypeloader_cache
from pypyr.cache.parsercache import contextparser_cache
from pypyr.cache.pipelinecache import pipeline_cache
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          PyModuleNotFoundError,
                          Stop,
                          StopPipeline)
import pypyr.moduleloader
import pypyr.pipelinerunner
from tests.common.utils import DeepCopyMagicMock


# ------------------------- parser mocks -------------------------------------#
from tests.common.utils import patch_logger


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
    contextparser_cache.clear()
    mocked_moduleloader.return_value.get_parsed_context = mock_parser

    context = pypyr.pipelinerunner.get_parsed_context(
        {'context_parser': 'specifiedparserhere'}, 'in arg here')

    mocked_moduleloader.assert_called_once_with('specifiedparserhere')

    assert isinstance(context, Context)
    assert len(context) == 2
    assert context['key1'] == 'created in mock parser'
    assert context['key2'] == 'in arg here'


@patch('pypyr.moduleloader.get_module', return_value=3)
def test_get_parser_context_signature_wrong(mocked_moduleloader):
    """Raise when parser found but no get_parsed_context attr."""
    contextparser_cache.clear()
    with pytest.raises(AttributeError) as err_info:
        pypyr.pipelinerunner.get_parsed_context(
            {'context_parser': 'specifiedparserhere'}, 'in arg here')

    assert str(err_info.value) == ("'int' object has no attribute "
                                   "'get_parsed_context'")

# ------------------------- get_parsed_context--------------------------------#

# ------------------------- main ---------------------------------------------#


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='arb/dir')
def test_main_pass(mocked_get_mocked_work_dir,
                   mocked_set_work_dir,
                   mocked_run_pipeline):
    """main initializes and runs pipelines."""
    pipeline_cache.clear()
    pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                              pipeline_context_input='arb context input',
                              working_dir='arb/dir',
                              log_level=77,
                              log_path=None,
                              groups=['g'],
                              success_group='sg',
                              failure_group='fg')

    mocked_set_work_dir.assert_called_once_with('arb/dir')
    mocked_run_pipeline.assert_called_once_with(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        groups=['g'],
        success_group='sg',
        failure_group='fg')


@patch('pypyr.pipelinerunner.load_and_run_pipeline',
       side_effect=ContextError('arb'))
@patch('pypyr.moduleloader.set_working_directory')
def test_main_fail(mocked_work_dir, mocked_run_pipeline):
    """main raises unhandled error on pipeline failure."""
    pipeline_cache.clear()
    with pytest.raises(ContextError) as err_info:
        pypyr.pipelinerunner.main(pipeline_name='arb pipe',
                                  pipeline_context_input='arb context input',
                                  working_dir='arb/dir',
                                  log_level=77,
                                  log_path=None)

    assert str(err_info.value) == "arb"

    mocked_work_dir.assert_called_once_with('arb/dir')
    mocked_run_pipeline.assert_called_once_with(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        groups=None,
        success_group=None,
        failure_group=None)

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


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'a': 'b'}))
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='arb/dir')
def test_load_and_run_pipeline_pass(mocked_get_work_dir,
                                    mocked_set_work_dir,
                                    mocked_get_pipe_def,
                                    mocked_get_parsed_context,
                                    mocked_steps_runner):
    """run_pipeline passes correct params to all methods."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    with patch('pypyr.context.Context') as mock_context:
        mock_context.return_value = Context()
        pypyr.pipelinerunner.load_and_run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input')

    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    # assure that freshly created context instance does have working dir set
    assert mock_context.return_value.working_dir == 'arb/dir'

    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={'a': 'b'})
    # No called steps, just on_failure since err on parse context already
    sr = mocked_steps_runner.return_value
    sr.run_step_groups.assert_called_once_with(groups=['steps'],
                                               success_group='on_success',
                                               failure_group='on_failure')
    sr.run_failure_step_group.assert_not_called()


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context())
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='arb/dir')
def test_load_and_run_pipeline_pass_skip_parse_context(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline passes correct params to all methods."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        parse_input=False)

    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_not_called()

    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={})
    # No called steps, just on_failure since err on parse context already
    sr = mocked_steps_runner.return_value
    sr.run_step_groups.assert_called_once_with(groups=['steps'],
                                               success_group='on_success',
                                               failure_group='on_failure')
    sr.run_failure_step_group.assert_not_called()


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context')
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='arb/dir')
def test_load_and_run_pipeline_parse_context_error(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline on_failure with empty Context if context parse fails."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    mocked_get_parsed_context.side_effect = ContextError

    with pytest.raises(ContextError):
        pypyr.pipelinerunner.load_and_run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input')

    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context=Context())
    # No called steps, just on_failure since err on parse context already
    sr = mocked_steps_runner.return_value
    sr.run_step_groups.assert_not_called()
    sr.run_failure_step_group.assert_called_once_with('on_failure')


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context())
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='arb/dir')
def test_load_and_run_pipeline_steps_error_raises(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline raises error if steps group fails."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    # First time it runs is steps - give a KeyNotInContextError.
    mocked_steps_runner.return_value.run_step_groups.side_effect = (
        KeyNotInContextError)

    with pytest.raises(KeyNotInContextError):
        pypyr.pipelinerunner.load_and_run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input')

    mocked_set_work_dir.assert_not_called()

    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='arb/dir')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='on_success',
        failure_group='on_failure'
    )
    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={})


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'1': 'context 1', '2': 'context2'}))
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='from/context')
def test_load_and_run_pipeline_with_existing_context_pass(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline passes correct params to all methods"""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    existing_context = Context({'2': 'original', '3': 'new'})
    existing_context.working_dir = 'from/context'

    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        context=existing_context)

    assert existing_context.working_dir == 'from/context'
    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='from/context')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='on_success',
        failure_group='on_failure'
    )
    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={'1': 'context 1',
                                                         '2': 'context2',
                                                         '3': 'new'})


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'1': 'context 1', '2': 'context2'}))
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='from/context')
def test_load_and_run_pipeline_with_group_specified(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline passes runs with specified group."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    existing_context = Context({'2': 'original', '3': 'new'})
    existing_context.working_dir = 'from/context'

    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        context=existing_context,
        groups=['arb1', 'arb2'])

    assert existing_context.working_dir == 'from/context'
    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='from/context')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['arb1', 'arb2'],
        success_group=None,
        failure_group=None
    )
    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={'1': 'context 1',
                                                         '2': 'context2',
                                                         '3': 'new'})


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'1': 'context 1', '2': 'context2'}))
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='from/context')
def test_load_and_run_pipeline_with_success_group_specified(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline passes runs with specified success group."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    existing_context = Context({'2': 'original', '3': 'new'})
    existing_context.working_dir = 'from/context'

    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        context=existing_context,
        success_group='arb1')

    assert existing_context.working_dir == 'from/context'
    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='from/context')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group='arb1',
        failure_group=None
    )
    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={'1': 'context 1',
                                                         '2': 'context2',
                                                         '3': 'new'})


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'1': 'context 1', '2': 'context2'}))
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='from/context')
def test_load_and_run_pipeline_with_failure_group_specified(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline passes runs with specified failure group."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    existing_context = Context({'2': 'original', '3': 'new'})
    existing_context.working_dir = 'from/context'

    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        context=existing_context,
        failure_group='arb1')

    assert existing_context.working_dir == 'from/context'
    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='from/context')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['steps'],
        success_group=None,
        failure_group='arb1'
    )
    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={'1': 'context 1',
                                                         '2': 'context2',
                                                         '3': 'new'})


@patch('pypyr.pipelinerunner.StepsRunner', autospec=True)
@patch('pypyr.pipelinerunner.get_parsed_context',
       return_value=Context({'1': 'context 1', '2': 'context2'}))
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
@patch('pypyr.moduleloader.set_working_directory')
@patch('pypyr.moduleloader.get_working_directory', return_value='from/context')
def test_load_and_run_pipeline_with_group_and_failure_group_specified(
        mocked_get_work_dir,
        mocked_set_work_dir,
        mocked_get_pipe_def,
        mocked_get_parsed_context,
        mocked_steps_runner):
    """run_pipeline passes runs with specified group and failure group."""
    pipeline_cache.clear()
    pypeloader_cache.clear()
    existing_context = Context({'2': 'original', '3': 'new'})
    existing_context.working_dir = 'from/context'

    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        context=existing_context,
        groups=['arb1'],
        failure_group='arb2')

    assert existing_context.working_dir == 'from/context'
    mocked_set_work_dir.assert_not_called()
    mocked_get_pipe_def.assert_called_once_with(pipeline_name='arb pipe',
                                                working_dir='from/context')
    mocked_get_parsed_context.assert_called_once_with(
        pipeline='pipe def',
        context_in_string='arb context input')

    mocked_steps_runner.return_value.run_step_groups.assert_called_once_with(
        groups=['arb1'],
        success_group=None,
        failure_group='arb2'
    )
    mocked_steps_runner.assert_called_once_with(pipeline_definition='pipe def',
                                                context={'1': 'context 1',
                                                         '2': 'context2',
                                                         '3': 'new'})
# ------------------------- run_pipeline -------------------------------------#

# ------------------------- loader -------------------------------------------#


def test_arbitrary_loader_module_not_found():
    with pytest.raises(PyModuleNotFoundError):
        pipeline_cache.clear()
        pypyr.moduleloader.set_working_directory('arb/dir')
        pypyr.pipelinerunner.load_and_run_pipeline(
            pipeline_name='arb pipe',
            pipeline_context_input='arb context input',
            loader='not_found_loader'
        )


def test_loader_no_get_pipeline_definition():
    """Arbitrary loader module without `get_pipeline_definition` function."""

    import sys
    current_module = sys.modules[__name__]

    pypyr.moduleloader.set_working_directory('arb/dir')

    with patch_logger(
            'pypyr.cache.loadercache',
            logging.ERROR) as mock_logger_error:
        with pytest.raises(AttributeError) as err:
            pypyr.pipelinerunner.load_and_run_pipeline(
                pipeline_name='arb pipe',
                pipeline_context_input='arb context input',
                loader=__name__)

    assert str(err.value) == f"module '{__name__}' " \
        "has no attribute 'get_pipeline_definition'"

    mock_logger_error.assert_called_once_with(
        f"The pipeline loader {current_module} doesn't have a "
        "get_pipeline_definition(pipeline_name, working_dir) function."
    )


@patch('pypyr.pipelinerunner.run_pipeline')
@patch('pypyr.pypeloaders.fileloader.get_pipeline_definition',
       return_value='pipe def')
def test_empty_loader_set_up_to_default(mock_get_pipeline_definition,
                                        mock_run_pipeline):
    """Default loader should be pypyr.pypeloaders.fileloader."""
    pypyr.moduleloader.set_working_directory('arb/dir')
    pipeline_cache.clear()
    pypeloader_cache.clear()
    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
    )

    mock_get_pipeline_definition.assert_called_once_with(
        pipeline_name='arb pipe',
        working_dir='arb/dir'
    )
    mock_run_pipeline.assert_called_once_with(
        context={},
        parse_input=True,
        pipeline='pipe def',
        pipeline_context_input='arb context input',
        groups=None,
        success_group=None,
        failure_group=None
    )


@patch('pypyr.pipelinerunner.run_pipeline')
def test_arb_loader(mock_run_pipeline):
    """Test loader set up"""
    pypyr.moduleloader.set_working_directory('tests')
    pipeline_cache.clear()
    pypyr.pipelinerunner.load_and_run_pipeline(
        pipeline_name='arb pipe',
        pipeline_context_input='arb context input',
        loader='arbpack.arbloader',
        groups=None,
        success_group=None,
        failure_group=None
    )

    mock_run_pipeline.assert_called_once_with(
        context={},
        parse_input=True,
        pipeline={'pipeline_name': 'arb pipe',
                  'working_dir': 'tests'},
        pipeline_context_input='arb context input',
        groups=None,
        success_group=None,
        failure_group=None
    )


# ------------------------- loader -------------------------------------------#

# ------------------------- Stop & StopPipeline ------------------------------#
def get_step_pipeline():
    """Test pipeline for jump."""
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
    pass


def stop_pipe_step(context):
    raise StopPipeline()


def stop_all_step(context):
    raise Stop()


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_pipeline(mock_step_cache):
    """StopPipeline stops pipeline execution."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 (StopPipeline)
    mock_step_cache.side_effect = [
        nothing_step,  # 2.1
        nothing_step,  # 2.2
        stop_pipe_step,  # 3.1
    ]

    context = Context()
    context.pipeline_name = 'arb'
    pypyr.pipelinerunner.run_pipeline(
        pipeline=get_step_pipeline(),
        context=context,
        pipeline_context_input='arb context input',
        groups=['sg2', 'sg3', 'sg4', 'sg1'],
        success_group='sg5',
        failure_group=None
    )

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_pipeline_for(mock_step_cache):
    """StopPipeline stops pipeline execution in for loop."""
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

    context = Context()
    context.pipeline_name = 'arb'
    pypyr.pipelinerunner.run_pipeline(
        pipeline=get_for_step_pipeline(),
        context=context,
        pipeline_context_input='arb context input',
        groups=['sg2', 'sg3', 'sg4', 'sg1'],
        success_group='sg5',
        failure_group=None
    )

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


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_pipeline_retry(mock_step_cache):
    """StopPipeline stops pipeline execution in retry loop."""
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

    context = Context()
    context.pipeline_name = 'arb'
    pypyr.pipelinerunner.run_pipeline(
        pipeline=get_retry_step_pipeline(),
        context=context,
        pipeline_context_input='arb context input',
        groups=['sg2', 'sg3', 'sg4', 'sg1'],
        success_group='sg5',
        failure_group=None
    )

    assert nothing_mock.mock_calls == [call({}),
                                       call({})
                                       ]

    assert mock312.mock_calls == [call({'retryCounter': 1}),
                                  call({'retryCounter': 2})]

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


@patch('pypyr.cache.stepcache.step_cache.get_step')
@patch('pypyr.cache.pipelinecache.pipeline_cache.get_pipeline',
       return_value=get_step_pipeline())
def test_stop_all(mock_get_pipe_def, mock_step_cache):
    """Stop stops pipeline execution."""
    # Sequence: sg2 - sg2.1, 2.2
    #           sg3 - sg3.1 (StopPipeline)
    mock_step_cache.side_effect = [
        nothing_step,  # 2.1
        nothing_step,  # 2.2
        stop_all_step,  # 3.1
    ]

    pypyr.pipelinerunner.main(
        pipeline_name='arb',
        pipeline_context_input='arb context input',
        working_dir='/arb',
        log_level=10,
        log_path=None,
        groups=['sg2', 'sg3', 'sg4', 'sg1'],
        success_group='sg5',
        failure_group=None
    )

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]


def get_while_step_pipeline():
    """Test pipeline for while."""
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
    }


@patch('pypyr.cache.stepcache.step_cache.get_step')
@patch('pypyr.cache.pipelinecache.pipeline_cache.get_pipeline',
       return_value=get_while_step_pipeline())
def test_stop_all_while(mock_get_pipe_def, mock_step_cache):
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

    pypyr.pipelinerunner.main(
        pipeline_name='arb',
        pipeline_context_input='arb context input',
        working_dir='/arb',
        log_level=10,
        log_path=None,
        groups=['sg2', 'sg3', 'sg4', 'sg1'],
        success_group='sg5',
        failure_group=None
    )

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


@patch('pypyr.cache.stepcache.step_cache.get_step')
@patch('pypyr.cache.pipelinecache.pipeline_cache.get_pipeline',
       return_value=get_for_step_pipeline())
def test_stop_all_for(mock_get_pipe_def, mock_step_cache):
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

    pypyr.pipelinerunner.main(
        pipeline_name='arb',
        pipeline_context_input='arb context input',
        working_dir='/arb',
        log_level=10,
        log_path=None,
        groups=['sg2', 'sg3', 'sg4', 'sg1'],
        success_group='sg5',
        failure_group=None
    )

    assert mock_step_cache.mock_calls == [call('sg2.step1'),
                                          call('sg2.step2'),
                                          call('sg3.step1')
                                          ]

    assert nothing_mock.mock_calls == [call({}),
                                       call({})
                                       ]

    assert mock312.mock_calls == [call({'i': 'one'}),
                                  call({'i': 'two'})]
# ------------------------- END Stop & StopPipeline --------------------------#
