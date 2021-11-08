"""pipelinerunner.py integration tests."""
import logging
from pathlib import Path
from unittest.mock import call

import pytest

from pypyr.cache.loadercache import loader_cache
from pypyr.errors import KeyNotInContextError
from pypyr import pipelinerunner

from tests.common.utils import patch_logger

working_dir_tests = Path.cwd().joinpath('tests')


@pytest.fixture
def pipeline_cache_reset():
    """Invoke for every test function in the module."""
    loader_cache.clear()
    yield
    loader_cache.clear()

# region smoke


def test_pipeline_runner_main(pipeline_cache_reset):
    """Smoke test for pipeline runner main.

    Strictly speaking this is an integration test, not a unit test.
    """
    pipelinerunner.run(pipeline_name='tests/pipelines/smoke',
                       args_in=None,
                       py_dir=working_dir_tests)
# endregion smoke

# region main


def test_pipeline_runner_main_all(pipeline_cache_reset):
    """Run main with all arguments as expected."""
    expected_notify_output = ['sg1', 'sg1.2', 'success_handler']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        pipelinerunner.run(
            # this path works because naiveloader checks from tests subdir.
            pipeline_name='pipelines/api/main-all',
            args_in=['A', 'B', 'C'],
            groups=['sg1'],
            success_group='sh',
            failure_group='fh',
            loader='arbpack.naivefileloader',
            py_dir=working_dir_tests)

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_all_with_failure(pipeline_cache_reset):
    """Run main with all arguments as expected with runtime error."""
    expected_notify_output = ['sg2', 'success_handler', 'fh']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        with pytest.raises(ValueError) as err:
            pipelinerunner.run(
                pipeline_name='pipelines/api/main-all',
                args_in=['A', 'B', 'C', 'raise on sh'],
                groups=['sg2'],
                success_group='sh',
                failure_group='fh',
                loader='arbpack.naivefileloader',
                py_dir=working_dir_tests)

    assert str(err.value) == "err from sh"
    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_minimal():
    """Run main with minimal arguments as expected."""
    expected_notify_output = ['steps', 'argList==None', 'on_success']

    # working_dir will default to repo root rather than test root
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        pipelinerunner.run('tests/pipelines/api/main-all')

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_with_failure():
    """Run main with failure argument as expected."""
    expected_notify_output = ['sg3', 'fh']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        with pytest.raises(ValueError) as err:
            pipelinerunner.run(
                pipeline_name='tests/pipelines/api/main-all',
                groups=['sg3'],
                failure_group='fh')

    assert str(err.value) == "err from sg3"
    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_minimal_with_failure_handled():
    """Run main minimal with failure argument as expected."""
    expected_notify_output = ['steps', 'on_success', 'on_failure']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        pipelinerunner.run(
            pipeline_name='tests/pipelines/api/main-all',
            args_in=['A', 'B', 'C', 'raise on success'])

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_with_failure_handled():
    """Run main with failure argument as expected."""
    expected_notify_output = ['sg3', 'on_failure']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        pipelinerunner.run(pipeline_name='tests/pipelines/api/main-all',
                           groups=['sg3'],
                           failure_group='on_failure')

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]

# endregion main

# region main_with_context


def test_pipeline_runner_main_with_context_all(pipeline_cache_reset):
    """Run main with context with all arguments as expected."""
    expected_notify_output = ['sg1', 'sg1.2', 'success_handler']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        out = pipelinerunner.run(
            pipeline_name='pipelines/api/main-all',
            dict_in={'argList': ['A', 'B', 'C']},
            # parse_args=False,
            groups=['sg1'],
            success_group='sh',
            failure_group='fh',
            loader='arbpack.naivefileloader',
            py_dir=working_dir_tests)

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]
    assert out == {'argList': ['A', 'B', 'C'], 'set_in_pipe': 123}


def test_pipeline_runner_main_with_context_all_with_failure(
        pipeline_cache_reset):
    """Run main with context - all arguments as expected with runtime error."""
    expected_notify_output = ['sg2', 'success_handler', 'fh']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        with pytest.raises(ValueError) as err:
            pipelinerunner.run(
                pipeline_name='pipelines/api/main-all',
                dict_in={'argList': ['A', 'B', 'C', 'raise on sh']},
                groups=['sg2'],
                success_group='sh',
                failure_group='fh',
                loader='arbpack.naivefileloader',
                py_dir=working_dir_tests)

    assert str(err.value) == "err from sh"
    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_with_context_minimal():
    """Run main with context with minimal arguments as expected."""
    # Not having argList==None proves context_parser didn't run.
    expected_notify_output = ['steps', 'argList==None', 'on_success']

    # working_dir will default to repo root rather than test root
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        out = pipelinerunner.run('tests/pipelines/api/main-all')

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]

    assert out == {'argList': [], 'set_in_pipe': 456}
    # somewhat arbitrary check if behaves like Context()
    out.assert_key_has_value('set_in_pipe', 'caller')


def test_pipeline_runner_main_with_context_with_failure():
    """Run main with context with failure argument as expected."""
    expected_notify_output = ['sg3', 'fh']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        with pytest.raises(ValueError) as err:
            pipelinerunner.run(
                pipeline_name='tests/pipelines/api/main-all',
                groups=['sg3'],
                failure_group='fh')

    assert str(err.value) == "err from sg3"
    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def test_pipeline_runner_main_with_context_relative_working_dir(
        pipeline_cache_reset):
    """Run main with context with relative working directory."""
    expected_notify_output = ['steps', 'on_success', 'on_failure']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        out = pipelinerunner.run(
            pipeline_name='tests/pipelines/api/main-all',
            dict_in={'argList': ['A', 'B', 'C', 'raise on success']})

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]

    assert len(out) == 4
    assert out['argList'] == ['A', 'B', 'C', 'raise on success']
    assert out['set_in_pipe'] == 456
    assert out['py'] == "raise ValueError('err from on_success')"

    assert len(out['runErrors']) == 1
    out_run_error = out['runErrors'][0]
    assert out_run_error
    assert out_run_error['col'] == 5
    assert out_run_error['customError'] == {}
    assert out_run_error['description'] == 'err from on_success'
    assert repr(out_run_error['exception']) == repr(ValueError(
        'err from on_success'))
    assert out_run_error['line'] == 74
    assert out_run_error['name'] == 'ValueError'
    assert out_run_error['step'] == 'pypyr.steps.py'
    assert out_run_error['swallowed'] is False
    # somewhat arbitrary check if behaves like Context()
    out.assert_key_has_value('set_in_pipe', 'caller')


def test_pipeline_runner_main_with_context_minimal_with_failure_handled():
    """Run main with context minimal with failure argument as expected."""
    expected_notify_output = ['steps', 'on_success', 'on_failure']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        out = pipelinerunner.run(
            pipeline_name='tests/pipelines/api/main-all',
            dict_in={'argList': ['A', 'B', 'C', 'raise on success']})

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]

    assert len(out) == 4
    assert out['argList'] == ['A', 'B', 'C', 'raise on success']
    assert out['set_in_pipe'] == 456
    assert out['py'] == "raise ValueError('err from on_success')"

    assert len(out['runErrors']) == 1
    out_run_error = out['runErrors'][0]
    assert out_run_error
    assert out_run_error['col'] == 5
    assert out_run_error['customError'] == {}
    assert out_run_error['description'] == 'err from on_success'
    assert repr(out_run_error['exception']) == repr(ValueError(
        'err from on_success'))
    assert out_run_error['line'] == 74
    assert out_run_error['name'] == 'ValueError'
    assert out_run_error['step'] == 'pypyr.steps.py'
    assert out_run_error['swallowed'] is False
    # somewhat arbitrary check if behaves like Context()
    out.assert_key_has_value('set_in_pipe', 'caller')


def test_pipeline_runner_main_with_context_with_failure_handled():
    """Run main with context with failure argument as expected."""
    expected_notify_output = ['sg3', 'on_failure']
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        out = pipelinerunner.run(
            pipeline_name='tests/pipelines/api/main-all',
            groups=['sg3'],
            failure_group='on_failure')

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]

    # extra context items is argList: []
    assert len(out) == 3
    assert out['py'] == "raise ValueError('err from sg3')"

    assert len(out['runErrors']) == 1
    out_run_error = out['runErrors'][0]
    assert out_run_error
    assert out_run_error['col'] == 5
    assert out_run_error['customError'] == {}
    assert out_run_error['description'] == 'err from sg3'
    assert repr(out_run_error['exception']) == repr(ValueError('err from sg3'))
    assert out_run_error['line'] == 50
    assert out_run_error['name'] == 'ValueError'
    assert out_run_error['step'] == 'pypyr.steps.py'
    assert out_run_error['swallowed'] is False

    # somewhat arbitrary check if behaves like Context()
    with pytest.raises(KeyNotInContextError) as err:
        out.assert_key_has_value('set_in_pipe', 'arbcaller')

    assert str(err.value) == ("context['set_in_pipe'] doesn't exist. It must "
                              "exist for arbcaller.")

# endregion main_with_context
