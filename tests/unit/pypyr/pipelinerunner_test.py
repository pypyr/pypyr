"""pipelinerunner.py unit tests."""
from unittest.mock import patch

import pytest

from pypyr.context import Context
from pypyr.errors import (ContextError)
from pypyr.pipelinerunner import run


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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


@patch('pypyr.pipelinerunner.Pipeline', autospec=True)
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
