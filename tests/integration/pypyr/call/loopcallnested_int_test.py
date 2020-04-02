"""Nested calls inside loops. These pipelines are in ./tests/pipelines/."""
import tests.common.pipeline_runner as test_pipe_runner


expected_file_name = '{0}_expected_output.txt'


def test_pipeline_nested():
    """Nested call control-of-flow works."""
    pipename = 'call/nested'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)

# ------------------------- for ----------------------------------------------#


def test_pipeline_nested_for():
    """Nested call control-of-flow works with for loop."""
    pipename = 'call/nestedfor'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


def test_pipeline_nested_for_deep():
    """Deep nested call control-of-flow works with for loop."""
    pipename = 'call/nestedfordeep'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


def test_pipeline_nested_for_groups_from_iterators():
    """Nested call control-of-flow works with groups set from iterators."""
    pipename = 'call/nestedforgroupsfromiterator'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


def test_pipeline_nested_for_formatted_groups():
    """Nested call control-of-flow works with groups set dynamically."""
    pipename = 'call/nestedforformatted'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)

# ------------------------- for ----------------------------------------------#

# ------------------------- while --------------------------------------------#


def test_pipeline_nested_while():
    """Nested call control-of-flow works with while loop."""
    pipename = 'call/nestedwhile'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


def test_pipeline_nested_while_swallow():
    """Nested call control-of-flow works with while loop swallowing errors."""
    pipename = 'call/nestedwhileswallow'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


def test_pipeline_nested_while_for():
    """Nested call control-of-flow works with while loop AND foreach."""
    pipename = 'call/nestedwhilefor'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)


def test_pipeline_nested_while_for_retry():
    """Nested call control-of-flow works with while AND foreach AND retry."""
    pipename = 'call/nestedwhileforretry'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)

# ------------------------- while --------------------------------------------#

# ------------------------- retries ------------------------------------------#


def test_pipeline_nested_retries():
    """Nested call control-of-flow works with while loop."""
    pipename = 'call/nestedretries'
    expected = expected_file_name.format(pipename)
    test_pipe_runner.assert_pipeline_notify_match_file(pipename, expected)

# ------------------------- retries ------------------------------------------#
