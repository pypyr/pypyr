"""Runs a pipeline in ./tests/pipelines."""
import logging
from pathlib import Path
from unittest.mock import call
import pypyr.pipelinerunner
from tests.common.utils import patch_logger, read_file_to_list
# ------------------------- for ----------------------------------------------#

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
