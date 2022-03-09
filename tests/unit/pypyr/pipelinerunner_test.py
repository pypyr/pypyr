"""pipelinerunner.py unit tests."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from pypyr.context import Context
from pypyr.errors import (ConfigError, ContextError)
from pypyr.pipeline import Pipeline
from pypyr.pipelinerunner import run

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

    monkeypatch.setattr('pypyr.pipelinerunner.Pipeline.new_pipe_and_args',
                        new_pipe_and_args_wrapper(mock_pipe))

    return mock_pipe


# endregion fixtures

# region run

def test_run_all(mock_pipe):
    """Run with maximal args in."""
    out = run(pipeline_name='arb pipe',
              args_in='arb context input',
              parse_args=True,
              dict_in={'a': 'b'},
              groups=['g'],
              success_group='sg',
              failure_group='fg',
              loader='arb loader',
              py_dir='arb/dir')

    assert type(out) is Context
    assert out == Context({'a': 'b'})
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args='arb context input',
        parse_input=True,
        groups=['g'],
        success_group='sg',
        failure_group='fg',
        loader='arb loader',
        py_dir='arb/dir'
    )

    mock_pipe.return_value.run.assert_called_once_with(out)


def test_run_minimal(mock_pipe):
    """Run with minimal args in."""
    out = run('arb pipe')

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=None,
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with(out)


def test_run_no_parse_when_dict_and_no_args_in(mock_pipe):
    """Default parse to false when dict_in exists and no args_in."""
    out = run('arb pipe', dict_in={'a': 'b'})

    assert type(out) is Context
    assert out == {'a': 'b'}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=None,
        parse_input=False,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with({'a': 'b'})


def test_run_parse_when_dict_and_args_in(mock_pipe):
    """Default parse to true when dict_in exists and args_in too."""
    out = run('arb pipe', args_in=['one', 'two'], dict_in={'a': 'b'})

    assert type(out) is Context
    assert out == {'a': 'b'}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=['one', 'two'],
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with({'a': 'b'})


def test_run_parse_when_no_dict_and_args_in(mock_pipe):
    """Default parse to true when dict_in doesn't exists and args_in does."""
    out = run('arb pipe', args_in=['one', 'two'])

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=['one', 'two'],
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with({})


def test_run_parse_when_no_dict_and_no_args_in(mock_pipe):
    """Default parse to true when dict_in doesn't exists and no args_in."""
    out = run('arb pipe')

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=None,
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with({})


def test_run_parse_when_parse_args_true(mock_pipe):
    """Always run parse when parse args explicitly true."""
    out = run('arb pipe', parse_args=True, dict_in={'a': 'b'})

    assert type(out) is Context
    assert out == {'a': 'b'}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=None,
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with({'a': 'b'})


def test_no_parse_when_parse_args_false(mock_pipe):
    """Never run parse when parse args explicitly true."""
    out = run('arb pipe', args_in=['one', 'two'], parse_args=False)

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args=['one', 'two'],
        parse_input=False,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with({})


def test_run_raises(mock_pipe):
    """Run raises unhandled error on pipeline failure."""
    mock_pipe.return_value.run.side_effect = ContextError('arb')

    with pytest.raises(ContextError) as err_info:
        run(pipeline_name='arb pipe',
            args_in='arb context input',
            py_dir='arb/dir')

    assert str(err_info.value) == 'arb'

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args='arb context input',
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir='arb/dir'
    )

    mock_pipe.return_value.run.assert_called_once_with({})

# endregion run

# region shortcuts


def test_run_shortcut_not_found(mock_pipe, monkeypatch):
    """Shortcuts configured but requested shortcut not found."""
    shortcuts = {'xxx': {
        'pipeline_name': 'sc pipe'
    }}
    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe',
              args_in='arb context input',
              parse_args=True,
              dict_in={'a': 'b'},
              groups=['g'],
              success_group='sg',
              failure_group='fg',
              loader='arb loader',
              py_dir='arb/dir')

    assert type(out) is Context
    assert out == Context({'a': 'b'})
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='arb pipe',
        context_args='arb context input',
        parse_input=True,
        groups=['g'],
        success_group='sg',
        failure_group='fg',
        loader='arb loader',
        py_dir='arb/dir'
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    assert shortcuts == {'xxx': {
        'pipeline_name': 'sc pipe'
    }}


def test_run_shortcut_all(mock_pipe, monkeypatch):
    """Run shortcut with maximal shortcut options."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'parser_args': ['sc', 'context', 'input'],
        'skip_parse': False,
        'args': {'a': 'updated', 'c': 'd'},
        'groups': ['sc g'],
        'success': 'sc sg',
        'failure': 'sc fg',
        'loader': 'sc loader',
        'py_dir': 'sc/dir'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe')

    assert type(out) is Context
    assert out == Context({'a': 'updated', 'c': 'd'})
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=['sc', 'context', 'input'],
        parse_input=True,
        groups=['sc g'],
        success_group='sc sg',
        failure_group='sc fg',
        loader='sc loader',
        py_dir=Path('sc/dir')
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'parser_args': ['sc', 'context', 'input'],
        'skip_parse': False,
        'args': {'a': 'updated', 'c': 'd'},
        'groups': ['sc g'],
        'success': 'sc sg',
        'failure': 'sc fg',
        'loader': 'sc loader',
        'py_dir': 'sc/dir'
    }}


def test_run_shortcut_all_ignore_func_args(mock_pipe, monkeypatch):
    """Run shortcut with maximal args superseding func args."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'parser_args': ['sc', 'context', 'input'],
        'skip_parse': False,
        'args': {'a': 'b', 'c': 'd'},
        'groups': ['sc g'],
        'success': 'sc sg',
        'failure': 'sc fg',
        'loader': 'sc loader',
        'py_dir': 'sc/dir'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe',
              args_in=['arb', 'context', 'input'],
              parse_args=True,
              dict_in={'a': 'updated', 'e': 'f'},
              groups=['g'],
              success_group='sg',
              failure_group='fg',
              loader='arb loader',
              py_dir='arb/dir')

    assert type(out) is Context
    assert out == Context({'a': 'updated', 'c': 'd', 'e': 'f'})
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=['sc', 'context', 'input', 'arb', 'context', 'input'],
        parse_input=True,
        groups=['sc g'],
        success_group='sc sg',
        failure_group='sc fg',
        loader='sc loader',
        py_dir=Path('sc/dir')
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'parser_args': ['sc', 'context', 'input'],
        'skip_parse': False,
        'args': {'a': 'b', 'c': 'd'},
        'groups': ['sc g'],
        'success': 'sc sg',
        'failure': 'sc fg',
        'loader': 'sc loader',
        'py_dir': 'sc/dir'
    }}


def test_run_shortcut_minimal_fallback_func_args(mock_pipe, monkeypatch):
    """Run shortcut with not set args overwritten by func args."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe',
              args_in=['arb', 'context', 'input'],
              parse_args=True,
              dict_in={'a': 'b', 'e': 'f'},
              groups=['g'],
              success_group='sg',
              failure_group='fg',
              loader='arb loader',
              py_dir='arb/dir')

    assert type(out) is Context
    assert out == Context({'a': 'b', 'e': 'f'})
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=['arb', 'context', 'input'],
        parse_input=True,
        groups=['g'],
        success_group='sg',
        failure_group='fg',
        loader='arb loader',
        py_dir='arb/dir'
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe'}}


def test_run_shortcut_minimal(mock_pipe, monkeypatch):
    """Run shortcut with minimal inputs."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe')

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=None,
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe'
    }}


def test_run_shortcut_parse_args(mock_pipe, monkeypatch):
    """Run shortcut bypasses parse_args from func input."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe', parse_args=False)

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    # when neither parser_args and args set, default True on parse_input.
    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=None,
        parse_input=True,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe'
    }}


def test_run_shortcut_skip_parse(mock_pipe, monkeypatch):
    """Run shortcut with skip_parse true."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'skip_parse': True
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe')

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=None,
        parse_input=False,
        groups=None,
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'skip_parse': True
    }}


def test_run_shortcut_groups_str(mock_pipe, monkeypatch):
    """Run shortcut with str groups converting to list."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'groups': 'sc g'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)
    out = run(pipeline_name='arb pipe')

    assert type(out) is Context
    assert out == {}
    assert not out.is_in_pipeline_scope

    mock_pipe.assert_called_once_with(
        name='sc pipe',
        context_args=None,
        parse_input=True,
        groups=['sc g'],
        success_group=None,
        failure_group=None,
        loader=None,
        py_dir=None
    )

    mock_pipe.return_value.run.assert_called_once_with(out)

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'groups': 'sc g'
    }}


def test_run_shortcut_no_pipe_name(mock_pipe, monkeypatch):
    """Run shortcut raises friendly error if no pipe name."""
    shortcuts = {'arb pipe': {
        'pipeline_nameX': 'sc pipe'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)

    with pytest.raises(ConfigError) as err:
        run(pipeline_name='arb pipe')

    assert str(err.value) == (
        "shortcut 'arb pipe' has no pipeline_name set. You must set "
        "pipeline_name for this shortcut in config so that pypyr knows which "
        "pipeline to run.")

    mock_pipe.assert_not_called()

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_nameX': 'sc pipe'
    }}


def test_run_shortcut_parser_args_str_raises(mock_pipe, monkeypatch):
    """Run shortcut raises friendly error if pipeArg is string."""
    shortcuts = {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'parser_args': 'arb'
    }}

    monkeypatch.setattr('pypyr.config.config.shortcuts', shortcuts)

    with pytest.raises(ConfigError) as err:
        run(pipeline_name='arb pipe')

    assert str(err.value) == (
        "shortcut 'arb pipe' parser_args should be a list, not a string.")

    mock_pipe.assert_not_called()

    # run shouldn't mutate the shared original config
    assert shortcuts == {'arb pipe': {
        'pipeline_name': 'sc pipe',
        'parser_args': 'arb'
    }}
# endregion shortcuts
