"""tar.py unit tests."""
import logging
import pytest
from unittest.mock import call, patch
from pypyr.context import Context
from pypyr.errors import (
    ContextError,
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
            'args': {'a': 'b'},
            'out': 'out value',
            'pipeArg': 'argument here',
            'useParentContext': False,
            'skipParse': 'skip parse',
            'raiseError': 'raise err',
            'loader': 'test loader',
            'groups': ['gr'],
            'success': 'sg',
            'failure': 'fg'
        }
    })

    (pipeline_name,
     args,
     out,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'b'}
    assert out == 'out value'
    assert not use_parent_context
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
        'argsHere': {'a': '{pipeName}'},
        'outHere': 'out here',
        'argHere': 'argument here',
        'parentContext': False,
        'skipParse': 'skip parse',
        'raiseErr': 'raise err',
        'loaderHere': 'test loader',
        'groups': ['gr'],
        'success': 'sg',
        'failure': 'fg',
        'pype': {
            'name': '{pipeName}',
            'args': '{argsHere}',
            'out': '{outHere}',
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
     args,
     out,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'pipe name'}
    assert out == 'out here'
    assert not use_parent_context
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
     args,
     out,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert not args
    assert not out
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


def test_pype_get_args_not_a_dict():
    """When args not a dict raise."""
    context = Context({'pype': {'name': 'blah', 'args': 'arb'}})

    with pytest.raises(ContextError) as err_info:
        pype.get_arguments(context)

    assert str(err_info.value) == (
        "pypyr.steps.pype 'args' in the 'pype' context item "
        "must be a dict.")


def test_pype_get_out_set_with_use_parent_context():
    """When out is present useParentContext must be false."""
    context = Context({'pype': {'name': 'blah',
                                'out': 'arb',
                                'useParentContext': True}})

    with pytest.raises(ContextError) as err_info:
        pype.get_arguments(context)

    assert str(err_info.value) == (
        "pypyr.steps.pype pype.out is only "
        "relevant if useParentContext = False. If you're using the parent "
        "context, no need to have out args since their values will already be "
        "in context. If you're NOT using parent context and you've specified "
        "pype.args, just leave off the useParentContext key and it'll default "
        "to False under the hood, or set it to False yourself if you keep it "
        "in.")


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
     args,
     out,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert not args
    assert not out
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
     args,
     out,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert not args
    assert not out
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


def test_pype_get_args_no_parent_context():
    """If args set use_parent_context should default False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
        }
    })

    (pipeline_name,
     args,
     out,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     groups,
     success_group,
     failure_group) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'b'}
    assert not out
    assert not use_parent_context
    assert skip_parse
    assert raise_error
    assert not loader
    assert not groups
    assert not success_group
    assert not failure_group

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
def test_pype_use_parent_context_with_args(mock_run_pipeline):
    """pype use_parent_context True with args."""
    context = Context({
        'k1': 'v1',
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': True,
            'loader': 'test loader'
        }
    })
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    merged_context = {
        'a': 'b',
        'k1': 'v1',
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': True,
            'loader': 'test loader'
        }
    }
    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context=merged_context,
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
        context={},
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
def test_pype_args(mock_run_pipeline):
    """pype args used as context."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'}
        }
    })
    context.working_dir = 'arb/dir'
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input=None,
        context={'a': 'b'},
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_args_with_out(mock_run_pipeline):
    """pype args used as context with out."""
    context = Context({
        'parentkey': 'parentvalue',
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
            'out': 'a'
        }
    })
    context.working_dir = 'arb/dir'
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input=None,
        context={'a': 'b'},
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]

    assert context == {'parentkey': 'parentvalue',
                       'a': 'b',
                       'pype': {
                            'name': 'pipe name',
                            'args': {'a': 'b'},
                            'out': 'a'
                       }
                       }


@patch('pypyr.pipelinerunner.load_and_run_pipeline')
def test_pype_args_with_mapping_out(mock_run_pipeline):
    """pype args used as context with mapping out."""
    context = Context({
        'parentkey': 'parentvalue',
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'av', 'b': 'bv', 'c': 'cv'},
            'out': {'new-a': 'a',
                    'new-c': 'c'}
        }
    })
    context.working_dir = 'arb/dir'
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input=None,
        context={'a': 'av', 'b': 'bv', 'c': 'cv'},
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]

    assert context == {'parentkey': 'parentvalue',
                       'new-a': 'av',
                       'new-c': 'cv',
                       'pype': {
                           'name': 'pipe name',
                           'args': {'a': 'av', 'b': 'bv', 'c': 'cv'},
                           'out': {'new-a': 'a',
                                   'new-c': 'c'}
                       }
                       }


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

    context.working_dir = 'arb/dir'

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input='argument here',
        context={},
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

    context.working_dir = 'arb/dir'

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        pype.run_step(context)

    mock_run_pipeline.assert_called_once_with(
        pipeline_name='pipe name',
        pipeline_context_input=None,
        context={},
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


# ------------------------ write_child_context_to_parent --------------------

def test_write_child_context_to_parent_wrong_type():
    """When out not a str, list or dict raise."""

    with pytest.raises(ContextError) as err_info:
        pype.write_child_context_to_parent(3, None, None)

    assert str(err_info.value) == (
        "pypyr.steps.pype pype.out should be a string, or a list or a dict. "
        "Instead, it's a <class 'int'>")


def test_write_child_context_to_parent_string():
    """Single string writes single key to parent."""
    parent = Context({'a': 'b'})
    child = Context({'c': 'd',
                     'e': 'f'})

    pype.write_child_context_to_parent('c', parent, child)

    assert parent == {'a': 'b',
                      'c': 'd'}


def test_write_child_context_to_parent_list():
    """Single string writes list of keys to parent."""
    parent = Context({'a': 'b'})
    child = Context({'c': 'd',
                     'e': 'f',
                     'g': 'h'})

    pype.write_child_context_to_parent(['c', 'g'], parent, child)

    assert parent == {'a': 'b',
                      'c': 'd',
                      'g': 'h'}


def test_write_child_context_to_parent_dict():
    """Single string maps keys to parent."""
    parent = Context({'a': 'b'})
    child = Context({'c': 'd',
                     'e': 'f',
                     'g': 'h'})

    pype.write_child_context_to_parent({'new-c': 'c',
                                        'new-g': 'g'},
                                       parent,
                                       child)

    assert parent == {'a': 'b',
                      'new-c': 'd',
                      'new-g': 'h'}


def test_write_child_context_to_parent_dict_with_formatting():
    """Single string maps keys to parent and formats child."""
    parent = Context({'a': 'b'})
    child = Context({'c': 'd',
                     'e': 'f',
                     'g': 'h and {e}'})

    pype.write_child_context_to_parent({'new-c': 'c',
                                        'new-g': 'g'},
                                       parent,
                                       child)

    assert parent == {'a': 'b',
                      'new-c': 'd',
                      'new-g': 'h and f'}
# ------------------------ write_child_context_to_parent --------------------
