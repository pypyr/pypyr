"""Nested calls inside loops. These pipelines are in ./tests/pipelines/."""
import tests.common.pipeline_runner as test_pipe_runner
# ------------------------- for ----------------------------------------------#

expected_file_name = '{0}_expected_output.txt'


def test_pipeline_nested_for():
    """Nested jump control-of-flow works with for loop."""
    pipename = 'tests/pipelines/jump/nestedfor'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


# ------------------------- for ----------------------------------------------#
