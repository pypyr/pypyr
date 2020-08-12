"""Error handling integration tests. Pipelines are in ./tests/pipelines/."""
import tests.common.pipeline_runner as test_pipe_runner
# ------------------------- for ----------------------------------------------#

expected_file_name = '{0}_expected_output.txt'


def test_error_line_col_no():
    """Line + col numbers correct on error."""
    pipename = 'errors/line-col-no'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)

# ------------------------- for ----------------------------------------------#
