"""Runs a pipeline in ./tests/pipelines."""
import logging
from pathlib import Path
import pytest
from unittest.mock import call
import pypyr.pipelinerunner
from tests.common.utils import patch_logger, read_file_to_list

working_dir = Path.joinpath(Path.cwd(), 'tests')


def assert_pipeline_notify_output_is(pipeline_name, expected_notify_output):
    """Assert that the pipeline has the expected output to NOTIFY log.

    Args:
        pipeline_name: str. Name of pipeline to run. Relative to ./tests/
        expected_notify_output: list of str. Entirety of strings expected in
                                the NOTIFY level output during pipeline run.
    """
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        pypyr.pipelinerunner.main(pipeline_name=pipeline_name,
                                  pipeline_context_input=None,
                                  working_dir=working_dir)

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def assert_pipeline_notify_match_file(pipeline_name,
                                      expected_notify_output_path):
    """Assert that the pipeline has the expected output to NOTIFY log.

    Args:
        pipeline_name: str. Name of pipeline to run. Relative to ./tests/
        expected_notify_output_path: path-like. Path to text file containing
                                     expected output. Relative to working dir.
    """
    assert_pipeline_notify_output_is(
        pipeline_name,
        read_file_to_list(Path.joinpath(working_dir,
                                        'pipelines',
                                        expected_notify_output_path)))


def assert_pipeline_raises(pipeline_name,
                           expected_error,
                           expected_error_msg,
                           expected_notify_output,
                           context_arg=None):
    """Assert pipeline fails with expected NOTIFY output.

    Will fail if pipeline does NOT raise expected_error.

    Args:
        pipeline_name: str. Name of pipeline to run. Relative to ./tests/
        expected_error: type. Expected exception type.
        expected_error_msg: str. Expected exception msg.
        expected_notify_output: list of str. Entirety of strings expected in
                                the NOTIFY level output during pipeline run.
        context_arg: str. Context argument input.
    """
    with patch_logger('pypyr.steps.echo', logging.NOTIFY) as mock_log:
        with pytest.raises(expected_error) as actual_err:
            pypyr.pipelinerunner.main(pipeline_name=pipeline_name,
                                      pipeline_context_input=context_arg,
                                      working_dir=working_dir)

    if expected_error_msg:
        assert str(actual_err.value) == expected_error_msg

    assert mock_log.mock_calls == [call(v) for v in expected_notify_output]


def assert_pipeline_raises_match_file(pipeline_name,
                                      expected_error,
                                      expected_error_msg,
                                      expected_notify_output_path,
                                      context_arg=None):
    """Assert that the pipeline fails the expected output to NOTIFY log.

    Args:
        pipeline_name: str. Name of pipeline to run. Relative to ./tests/
        expected_notify_output_path: path-like. Path to text file containing
                                     expected output. Relative to working dir.
    """
    assert_pipeline_raises(
        pipeline_name,
        expected_error,
        expected_error_msg,
        read_file_to_list(Path.joinpath(working_dir,
                                        'pipelines',
                                        expected_notify_output_path)),
        context_arg)
