"""tar.py unit tests."""
import logging
import pytest
from unittest.mock import call, patch
from pypyr.context import Context
from pypyr.errors import (
    Stop,
    KeyInContextHasNoValueError,
    KeyNotInContextError)
import pypyr.steps.pype as pype

# ------------------------ get_arguments --------------------------------------
from tests.common.utils import patch_logger


def test_pype_get_arguments_all():
    """Parse all input from context."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': 'parent context bool',
            'skipParse': 'skip parse',
            'raiseError': 'raise err',
            'loader': 'test loader',
            'groups': ['gr'],
            'success': 'sg',
            'failure': 'fg'
        }
    })

    (pipeline_name,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert use_parent_context == 'parent context bool'
    assert skip_parse == 'skip parse'
    assert raise_error == 'raise err'
    assert loader == 'test loader'
    assert groups == ['gr']
    assert success_group == 'sg'
    assert failure_group == 'fg'


def test_pype_get_arguments_all_with_interpolation():
    """Parse all input from context."""
    context = Context({
        'pipeName': 'pipe name',
        'argHere': 'argument here',
        'parentContext': 'parent context bool',
        'skipParse': 'skip parse',
        'raiseErr': 'raise err',
        'loaderHere': 'test loader',
        'groups': ['gr'],
        'success': 'sg',
        'failure': 'fg',
        'pype': {
            'name': '{pipeName}',
            'pipeArg': '{argHere}',
            'useParentContext': '{parentContext}',
            'skipParse': '{skipParse}',
            'raiseError': '{raiseErr}',
            'loader': '{loaderHere}',
            'groups': '{groups}',
            'success': '{success}',
            'failure': '{failure}',
        }
    })

    (pipeline_name,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert use_parent_context == 'parent context bool'
    assert pipe_arg == 'argument here'
    assert skip_parse == 'skip parse'
    assert raise_error == 'raise err'
    assert loader == 'test loader'
    assert groups == ['gr']
    assert success_group == 'sg'
    assert failure_group == 'fg'


def test_pype_get_arguments_defaults():
    """Parse all input from context and assign defaults where not specified."""
    context = Context({
        'pype': {
            'name': 'pipe name'
        }
    })

    (pipeline_name,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert use_parent_context
    assert isinstance(use_parent_context, bool)
    assert skip_parse
    assert isinstance(skip_parse, bool)
    assert raise_error
    assert isinstance(raise_error, bool)
    assert loader is None
    assert groups is None
    assert success_group is None
    assert failure_group is None


def test_pype_get_arguments_missing_pype():
    """Missing pype throw."""
    context = Context()

    with pytest.raises(KeyNotInContextError) as err_info:
        pype.get_arguments(context)

    assert str(err_info.value) == ("context['pype'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.pype.")


def test_pype_get_arguments_missing_name():
    """Missing pype name throw."""
    context = Context({'pype': {}})

    with pytest.raises(KeyNotInContextError) as err_info:
        pype.get_arguments(context)

    assert str(err_info.value) == (
        "pypyr.steps.pype missing 'name' in the 'pype' "
        "context item. You need to specify the pipeline name to run another "
        "pipeline.")


def test_pype_get_arguments_name_empty():
    """Empty pype name throw."""
    context = Context({'pype': {'name': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        pype.get_arguments(context)

    assert str(err_info.value) == ("pypyr.steps.pype ['pype']['name'] exists "
                                   "but is empty.")


def test_pype_get_arguments_group_str():
    """Parse group as str input from context."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'groups': 'gr',
        }
    })

    (pipeline_name,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert use_parent_context
    assert isinstance(use_parent_context, bool)
    assert skip_parse
    assert isinstance(skip_parse, bool)
    assert raise_error
    assert isinstance(raise_error, bool)
    assert loader is None
    assert groups == ['gr']
    assert success_group is None
    assert failure_group is None


def test_pype_get_arguments_group_str_interpolate():
    """Parse group as interpolated str input from context."""
    context = Context({
        'group': 'gr',
        'pype': {
            'name': 'pipe name',
            'groups': '{group}',
        }
    })

    (pipeline_name,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert use_parent_context
    assert isinstance(use_parent_context, bool)
    assert skip_parse
    assert isinstance(skip_parse, bool)
    assert raise_error
    assert isinstance(raise_error, bool)
    assert loader is None
    assert groups == ['gr']
    assert success_group is None
    assert failure_group is None

# ------------------------ get_arguments --------------------------------------

# ------------------------ run_step -------------------------------------------


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_use_parent_context(mock_run_pipeline):
    """pype use_parent_context True."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': True,
            'loader': 'test loader'
        }
    })
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context=context,
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, using parent context.'),
        call('pyped pipe name.')]


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_no_parent_context(mock_run_pipeline):
    """pype use_parent_context False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': False,
            'skipParse': True,
            'raiseError': True,
            'loader': 'test loader',
        }
    })
    context.working_dir = 'arb/dir'
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_no_skip_parse(mock_run_pipeline):
    """pype use_parent_context False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': False,
            'skipParse': False,
            'raiseError': True
        }
    })

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        parse_input=True,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_no_pipe_arg(mock_run_pipeline):
    """pype use_parent_context False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': None,
            'useParentContext': False,
            'skipParse': False,
            'raiseError': True,
        }
    })

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input=None,
        parse_input=True,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


@patch('pypyr.pipelinerunner.load_and_run_pipeline',
       side_effect=RuntimeError('whoops'))
def test_pype_use_parent_context_no_swallow(mock_run_pipeline):
    """pype without swallowing error in child pipeline."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': True
        }
    })
    with patch_logger('pypyr.steps.pype', logging.ERROR) as mock_logger_error:
        with pytest.raises(RuntimeError) as err_info:
            pype.run_step(context)

        assert str(err_info.value) == "whoops"

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context=context,
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    mock_logger_error.assert_called_once_with(
        'Something went wrong pyping pipe name. RuntimeError: whoops')


@patch('pypyr.pipelinerunner.load_and_run_pipeline',
       side_effect=RuntimeError('whoops'))
def test_pype_use_parent_context_with_swallow(mock_run_pipeline):
    """pype swallowing error in child pipeline."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': False,
            'loader': 'test loader'
        }
    })
    with patch_logger('pypyr.steps.pype', logging.ERROR) as mock_logger_error:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context=context,
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None
    )

    mock_logger_error.assert_called_once_with(
        'Something went wrong pyping pipe name. RuntimeError: whoops')


@patch('pypyr.pipelinerunner.load_and_run_pipeline',
       side_effect=Stop())
def test_pype_use_parent_context_swallow_stop_error(mock_run_pipeline):
    """pype doesn't swallow stop error in child pipeline."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': False
        }
    })
    with patch_logger('pypyr.steps.pype', logging.ERROR) as mock_logger_error:
        with pytest.raises(Stop) as err_info:
            pype.run_step(context)

        assert isinstance(err_info.value, Stop)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context=context,
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    mock_logger_error.assert_not_called()


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_set_groups(mock_run_pipeline):
    """pype use_parent_context True."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': True,
            'loader': 'test loader',
            'groups': 'testgroup',
            'success': 'successgroup',
            'failure': 'failuregroup'
        }
    })
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context=context,
        parse_input=False,
        loader='test loader',
        groups=['testgroup'],
        success_group='successgroup',
        failure_group='failuregroup'
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, using parent context.'),
        call('pyped pipe name.')]
# ------------------------ run_step --------------------------------------
