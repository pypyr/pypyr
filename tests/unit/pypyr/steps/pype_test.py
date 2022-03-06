"""pype.py unit tests."""
import logging
from unittest.mock import call, Mock

import pytest

from pypyr.context import Context
from pypyr.errors import (
    ContextError,
    Stop,
    KeyInContextHasNoValueError,
    KeyNotInContextError)

from pypyr.pipeline import Pipeline
from pypyr.pipedef import PipelineDefinition, PipelineInfo
import pypyr.steps.pype as pype

from tests.common.utils import patch_logger

# region fixtures


def new_pipe_and_args_wrapper(mock_pipe):
    """Return ref to Pipeline new_pipe_and_args, overriding the cls arg.

    Reason is normal patch does not patch out the cls arg on a class method.

    Intercept the factory method, passing in a mock as type to instantiate.

    Args:
        mock_pipe: Replace the 1st arg (i.e cls) to the classmethod with me.
    """
    # get the reference to the underlying method before it's patched
    og_ref = Pipeline.new_pipe_and_args.__func__

    def new_pipe_and_args(*args, **kwargs):
        # the first arg is cls - for which we're substituting the mock
        return og_ref(mock_pipe, *args, **kwargs)

    return new_pipe_and_args


@pytest.fixture
def mock_pipe(monkeypatch):
    """Intercept Pipeline.new_pipe_and_args factory method."""
    mock_pipe = Mock(spec=Pipeline)
    mock_pipe._get_parse_input = Pipeline._get_parse_input

    monkeypatch.setattr('pypyr.steps.pype.Pipeline.new_pipe_and_args',
                        new_pipe_and_args_wrapper(mock_pipe))

    return mock_pipe


# endregion fixtures


def get_arb_pipeline_scope(context):
    """Context must be in pipeline scope to get current pipe info."""
    pipeline = Pipeline('arb pipe')
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=None,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))
    return context.pipeline_scope(pipeline)

# region get_arguments


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
            'failure': 'fg',
            'pyDir': 'arb/dir',
            'parent': 'the parent'
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'b'}
    assert out == 'out value'
    assert not use_parent_context
    assert skip_parse == 'skip parse'
    assert pipe_arg == ['argument', 'here']
    assert raise_error == 'raise err'
    assert loader == 'test loader'
    assert groups == ['gr']
    assert success_group == 'sg'
    assert failure_group == 'fg'
    assert py_dir == 'arb/dir'
    assert parent == 'the parent'


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
        'dir': 'arb/dir',
        'parent': 'the parent',
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
            'pyDir': '{dir}',
            'parent': '{parent}'
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'pipe name'}
    assert out == 'out here'
    assert not use_parent_context
    assert pipe_arg == ['argument', 'here']
    assert skip_parse == 'skip parse'
    assert raise_error == 'raise err'
    assert loader == 'test loader'
    assert groups == ['gr']
    assert success_group == 'sg'
    assert failure_group == 'fg'
    assert py_dir == 'arb/dir'
    assert parent == 'the parent'


def test_pype_get_arguments_defaults():
    """Parse all input from context and assign defaults where not specified."""
    context = Context({
        'pype': {
            'name': 'pipe name'
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args is None
    assert out is None
    assert use_parent_context
    assert isinstance(use_parent_context, bool)
    assert pipe_arg is None
    assert skip_parse
    assert isinstance(skip_parse, bool)
    assert raise_error
    assert isinstance(raise_error, bool)
    assert loader is None
    assert groups is None
    assert success_group is None
    assert failure_group is None
    assert py_dir is None
    # defaults to current pipeline's parent if cascading loader.
    assert parent is None


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

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args is None
    assert out is None
    assert use_parent_context
    assert isinstance(use_parent_context, bool)
    assert pipe_arg is None
    assert skip_parse
    assert isinstance(skip_parse, bool)
    assert raise_error
    assert isinstance(raise_error, bool)
    assert loader is None
    assert groups == ['gr']
    assert success_group is None
    assert failure_group is None
    assert py_dir is None
    assert parent is None


def test_pype_get_arguments_group_str_interpolate():
    """Parse group as interpolated str input from context."""
    context = Context({
        'group': 'gr',
        'pype': {
            'name': 'pipe name',
            'groups': '{group}',
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args is None
    assert out is None
    assert use_parent_context
    assert isinstance(use_parent_context, bool)
    assert pipe_arg is None
    assert skip_parse
    assert isinstance(skip_parse, bool)
    assert raise_error
    assert isinstance(raise_error, bool)
    assert loader is None
    assert groups == ['gr']
    assert success_group is None
    assert failure_group is None
    assert py_dir is None
    assert parent is None


def test_pype_get_args_no_parent_context():
    """If args set use_parent_context should default False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'b'}
    assert out is None
    assert not use_parent_context
    assert pipe_arg is None
    assert skip_parse
    assert raise_error
    assert not loader
    assert not groups
    assert not success_group
    assert not failure_group
    assert py_dir is None
    assert parent is None


def test_pype_get_pipeargs_no_skip_parse():
    """If pipeArgs set skipParse should default False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'a b c',
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args is None
    assert out is None
    assert not use_parent_context
    assert pipe_arg == ['a', 'b', 'c']
    assert not skip_parse
    assert raise_error
    assert not loader
    assert not groups
    assert not success_group
    assert not failure_group
    assert py_dir is None
    assert parent is None


def test_pype_get_args_and_pipearg():
    """Combine pipeArgs and args. Defaults useParentContext to False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
            'pipeArg': 'a b c',
        }
    })

    with get_arb_pipeline_scope(context):
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
         failure_group,
         py_dir,
         parent) = pype.get_arguments(context)

    assert pipeline_name == 'pipe name'
    assert args == {'a': 'b'}
    assert out is None
    assert not use_parent_context
    assert pipe_arg == ['a', 'b', 'c']
    assert not skip_parse
    assert raise_error
    assert not loader
    assert not groups
    assert not success_group
    assert not failure_group
    assert py_dir is None
    assert parent is None

# region cascading


def get_scope_from_info(context, info):
    """Context must be in pipeline scope to get current pipe info."""
    pipeline = Pipeline('arb pipe')
    pipeline.pipeline_definition = PipelineDefinition(pipeline=None, info=info)
    return context.pipeline_scope(pipeline)


def test_pype_gets_args_loader_non_cascading():
    """Loader not cascading."""
    context = Context({
        'pype': {
            'name': 'pipe name'
        }
    })

    info = PipelineInfo(pipeline_name='arb',
                        loader='arbloader',
                        parent='noncascading/dir',
                        is_loader_cascading=False)

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader is None
    assert pype_args.parent is None


def test_pype_get_args_parent_cascading():
    """Same loader as parent with cascade."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'loader': 'arbloader'
        }
    })

    info = PipelineInfo(pipeline_name='arb',
                        loader='arbloader',
                        parent='cascading/parent')

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader == 'arbloader'
    assert pype_args.parent == 'cascading/parent'


def test_pype_get_args_parent_not_cascading_parent():
    """A non-cascading loader does not cascade parent."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'loader': 'arbloader'
        }
    })

    info = PipelineInfo(pipeline_name='arb',
                        loader='arbloader',
                        parent='noncascading/dir',
                        is_parent_cascading=False)

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader == 'arbloader'
    assert pype_args.parent is None


def test_pype_get_args_parent_cascading_different_loader_set():
    """Do not cascade when different loader than parent."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'loader': 'arbloader1'
        }
    })

    info = PipelineInfo(
        pipeline_name='arb',
        loader='arbloader2',
        parent='cascading/dir')

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader == 'arbloader1'
    assert pype_args.parent is None


def test_pype_get_args_parent_cascade_no_loader_set():
    """No loader set on parent and no loader on pype with cascade.

    This is very edge. pypyr core will normalize loader=None to the file
    loader, and to use a custom loader the dev would have to pass a non-None
    to run()/load_and_run() to begin with.

    It shouldn't ever happen short of some heavy customization where a custom
    client loader explicitly sets None the loader property on the Info object.
    Which, why? But just in case, here's a test.
    """
    context = Context({
        'pype': {
            'name': 'pipe name'
        }
    })

    info = PipelineInfo(
        pipeline_name='arb',
        loader=None,
        parent='cascading/parent')

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader is None
    assert pype_args.parent == 'cascading/parent'


def test_pype_get_args_parent_cascade_no_loader_no_parent_set():
    """No loader+parent set on parent & no loader+parent on pype with cascade.

    This is very edge. pypyr core will normalize loader=None to the file
    loader, and to use a custom loader the dev would have to pass a non-None
    to run()/load_and_run() to begin with.

    It shouldn't ever happen short of some heavy customization where a custom
    client loader explicitly sets None the loader property on the Info object.
    Which, why? But just in case, here's a test.
    """
    context = Context({
        'pype': {
            'name': 'pipe name'
        }
    })

    info = PipelineInfo(
        pipeline_name='arb',
        loader=None,
        parent=None)

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader is None
    assert pype_args.parent is None


def test_pype_get_parent_set_on_cascading_loader():
    """Always use parent when set even if cascading loader."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'loader': 'arbloader',
            'parent': 'arb/from/child'
        }
    })

    info = PipelineInfo(pipeline_name='arb',
                        loader='arbloader',
                        parent='ignore me')

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader == 'arbloader'
    assert pype_args.parent == 'arb/from/child'


def test_pype_resolve_from_parent_false_on_cascading_loader():
    """Ignore loader is_parent_cascading when resolveFromParent False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'loader': 'arbloader',
            'resolveFromParent': False
        }
    })

    info = PipelineInfo(pipeline_name='arb',
                        loader='arbloader',
                        parent='ignore me')

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader == 'arbloader'
    assert pype_args.parent is None


def test_pype_resolve_from_parent_true_on_cascading_loader():
    """Ignore loader is_parent_cascading when resolveFromParent False."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'loader': 'arbloader',
            'resolveFromParent': True
        }
    })

    info = PipelineInfo(pipeline_name='arb',
                        loader='arbloader',
                        parent='from parent')

    with get_scope_from_info(context, info):
        pype_args = pype.get_arguments(context)

    assert pype_args.pipeline_name == 'pipe name'
    assert pype_args.loader == 'arbloader'
    assert pype_args.parent == 'from parent'

# endregion cascading

# endregion get_arguments

# region run_step


def mocked_run_pipeline(*args, **kwargs):
    """Check pipeline name set on context in child pipeline."""
    # assert (kwargs['name']
    #         == kwargs['context'].pipeline_name == 'pipe name')
    # assert (kwargs['pipeline_name'] == 'pipe name')
    pass


def test_pype_use_parent_context(mock_pipe):
    """Input pype use_parent_context True."""
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
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once_with(context, None)

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, using parent context.'),
        call('pyped pipe name.')]


def test_pype_use_parent_context_with_args(mock_pipe):
    """Input pype use_parent_context True with args."""
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
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    # args merges into context
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

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once_with(merged_context, None)

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, using parent context.'),
        call('pyped pipe name.')]


def test_pype_no_parent_context(mock_pipe):
    """Input pype use_parent_context False."""
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
    # context.parent = 'arb/dir'
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    # using empty/fresh new context
    mocked_runner.assert_called_once_with({}, None)

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


def test_pype_args(mock_pipe):
    """Input pype args used as context."""
    context = Context({
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'}
        }
    })

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=None,
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    # using args as context
    mocked_runner.assert_called_once_with({'a': 'b'}, None)


def test_pype_args_with_shortcut(mock_pipe, monkeypatch):
    """Input pype args merged into shortcut used as context."""
    shortcuts = {'pipe name': {
        'pipeline_name': 'sc pipe',
        'args': {
            'a': 'og',
            'c': ['d']
        }
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)

    context = Context({
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'}
        }
    })

    def l_and_r(context, parent):
        assert parent is None
        assert context == {'a': 'b', 'c': ['d']}
        context['c'].append('updated')
        context['e'] = 'new'

    mock_pipe.return_value.load_and_run_pipeline.side_effect = l_and_r

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=None,
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once()

    # original shortcut shouldn't mutate
    assert shortcuts == {'pipe name': {
        'pipeline_name': 'sc pipe',
        'args': {
            'a': 'og',
            'c': ['d']
        }
    }}

    # useParentContext is False, therfore no context mutations in parent.
    assert context == {
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'}
        }}


def test_pype_args_with_out(mock_pipe):
    """Input pype args used as context with out."""
    context = Context({
        'parentkey': 'parentvalue',
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'b'},
            'out': 'a'
        }
    })
    context.parent = 'arb/dir'
    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=None,
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    # using args as new context
    mocked_runner.assert_called_once_with({'a': 'b'}, None)

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


def test_pype_args_with_mapping_out(mock_pipe):
    """Input pype args used as context with mapping out."""
    context = Context({
        'parentkey': 'parentvalue',
        'pype': {
            'name': 'pipe name',
            'args': {'a': 'av', 'b': 'bv', 'c': 'cv'},
            'out': {'new-a': 'a',
                    'new-c': 'c'}
        }
    })

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=None,
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once_with({'a': 'av', 'b': 'bv', 'c': 'cv'},
                                          None)

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


def test_pype_no_skip_parse(mock_pipe):
    """Input pype use_parent_context False."""
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
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=True,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once_with({}, None)

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


def test_pype_no_pipe_arg(mock_pipe):
    """Input pype use_parent_context False."""
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
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=None,
        parse_input=True,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once_with({}, None)

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, without parent context.'),
        call('pyped pipe name.')]


def mocked_run_pipeline_with_runtime_error(*args, **kwargs):
    """Check pipeline name set on context in child pipeline with arb err."""
    assert (kwargs['pipeline_name']
            == kwargs['context'].pipeline_name == 'pipe name')
    assert (kwargs['pipeline_name'] == 'pipe name')
    raise RuntimeError('whoops')


def test_pype_use_parent_context_no_swallow(mock_pipe):
    """Input pype without swallowing error in child pipeline."""
    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.side_effect = RuntimeError('whoops')

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
            with get_arb_pipeline_scope(context):
                pype.run_step(context)

        assert str(err_info.value) == "whoops"

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner.assert_called_once_with({
        'pype': {
            'name': 'pipe name',
            'pipeArg': 'argument here',
            'useParentContext': True,
            'skipParse': True,
            'raiseError': True
        }
    }, None)

    mock_logger_error.assert_called_once_with(
        'Something went wrong pyping pipe name. RuntimeError: whoops')


def test_pype_use_parent_context_with_swallow(mock_pipe):
    """Input pype swallowing error in child pipeline."""
    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.side_effect = RuntimeError('whoops')

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
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader='test loader',
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner.assert_called_once_with(context, None)

    mock_logger_error.assert_called_once_with(
        'Something went wrong pyping pipe name. RuntimeError: whoops')


def mocked_run_pipeline_with_stop(*args, **kwargs):
    """Check pipeline name set on context in child pipeline with Stop."""
    assert (kwargs['pipeline_name']
            == kwargs['context'].pipeline_name == 'pipe name')
    assert (kwargs['pipeline_name'] == 'pipe name')
    raise Stop()


def test_pype_use_parent_context_swallow_stop_error(mock_pipe):
    """Input pype doesn't swallow stop error in child pipeline."""
    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.side_effect = Stop()
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
            with get_arb_pipeline_scope(context):
                pype.run_step(context)

        assert isinstance(err_info.value, Stop)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader=None,
        groups=None,
        success_group=None,
        failure_group=None,
        py_dir=None
    )

    mocked_runner.assert_called_once_with(context, None)

    mock_logger_error.assert_not_called()


def test_pype_set_groups(mock_pipe):
    """Input pype with groups set."""
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
            'failure': 'failuregroup',
            'pyDir': 'test dir'
        }
    })

    with patch_logger('pypyr.steps.pype', logging.INFO) as mock_logger_info:
        with get_arb_pipeline_scope(context):
            pype.run_step(context)

    mock_pipe.assert_called_once_with(
        name='pipe name',
        context_args=['argument', 'here'],
        parse_input=False,
        loader='test loader',
        groups=['testgroup'],
        success_group='successgroup',
        failure_group='failuregroup',
        py_dir='test dir'
    )

    mocked_runner = mock_pipe.return_value.load_and_run_pipeline
    mocked_runner.assert_called_once_with(context, None)

    assert mock_logger_info.mock_calls == [
        call('pyping pipe name, using parent context.'),
        call('pyped pipe name.')]
# endregion run_step


# region write_child_context_to_parent

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
# endregion write_child_context_to_parent
