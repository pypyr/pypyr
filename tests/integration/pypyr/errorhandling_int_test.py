"""Error handling integration tests. Pipelines in ./tests/pipelines/errors."""
import tests.common.pipeline_runner as test_pipe_runner
# region runErrors

expected_file_name = '{0}_expected_output.txt'


def test_error_line_col_no():
    """Line + col numbers correct on error."""
    pipename = 'tests/pipelines/errors/line-col-no'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename, ['done'])

# endregion runErrors

# region failure handler


def test_fail_no_handler():
    """No failure handler exits pypyr with exception."""
    pipename = 'tests/pipelines/errors/fail-no-handler'
    test_pipe_runner.assert_pipeline_raises(pipename,
                                            ValueError,
                                            'arb',
                                            ['A'])


def test_fail_handler():
    """Failure handler exits pypyr with exception."""
    pipename = 'tests/pipelines/errors/fail-handler'
    test_pipe_runner.assert_pipeline_raises(pipename,
                                            ValueError,
                                            'arb',
                                            ['A', 'B'])


def test_fail_handler_also_fails():
    """Failure handler also fails & exits pypyr with original exception."""
    pipename = 'tests/pipelines/errors/fail-handler-also-fails'
    test_pipe_runner.assert_pipeline_raises(pipename,
                                            TypeError,
                                            'O.G err',
                                            ['A'])


def test_fail_handler_stop():
    """Failure handler with Stop exits pypyr with no exception."""
    pipename = 'tests/pipelines/errors/fail-handler-stop'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename, ['A'])


def test_fail_handler_stoppipeline():
    """Failure handler with StopPipeline exits pypyr with no exception."""
    pipename = 'tests/pipelines/errors/fail-handler-stoppipeline'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename, ['A'])


def test_fail_handler_stoppipeline_pype_nested():
    """Failure handler can call to other pipelines and still stop.

    Parent pipeline has its own failure-handler, which can also stop.
    """
    pipename = 'tests/pipelines/errors/fail-handler-stoppipeline-pype-nested'
    test_pipe_runner.assert_pipeline_notify_output_is(
        pipename,
        ['A.parent', 'A', 'B.parent', 'C.parent'])


def test_fail_handler_stopstepgroup():
    """Failure handler with StopStepGroup exits pypyr with no exception."""
    pipename = 'tests/pipelines/errors/fail-handler-stopstepgroup'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename, ['A'])


def test_fail_handler_stopstepgroup_multi():
    """Failure handler with StopStepGroup exits pypyr with no exception.

    Only calls 1st group in call.
    """
    pipename = 'tests/pipelines/errors/fail-handler-stopstepgroup-multi'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename,
                                                      ['A', 'B', 'C'])


def test_fail_handler_stop_call_on_failure_fallback():
    """Failure handler with Stop exits pypyr with no exception.

    Only calls 1st group in call. Call with no failure handler
    falls back to default on_failure on pipeline level.
    """
    p = 'tests/pipelines/errors/fail-handler-stop-call-on-failure-fallback'
    test_pipe_runner.assert_pipeline_notify_output_is(p, ['A', 'B'])


def test_fail_handler_call_from_handler():
    """Failure handler can call to other stepgroups.

    Still raises at end.
    """
    pipename = 'tests/pipelines/errors/fail-handler-call-from-handler'
    test_pipe_runner.assert_pipeline_raises(pipename,
                                            AssertionError,
                                            'assert False evaluated to False.',
                                            ['A', 'B', 'C', 'D', 'E'])


def test_fail_handler_call_from_handler_nest_fail():
    """Failure handler can call to other stepgroups.

    Called step-group has its own failure handler.
    """
    p = 'tests/pipelines/errors/fail-handler-call-from-handler-nest-fail'
    test_pipe_runner.assert_pipeline_raises(p,
                                            AssertionError,
                                            'assert False evaluated to False.',
                                            ['A', 'B', 'C', 'D'])


def test_fail_handler_call_from_handler_nest_fail_handler():
    """Failure handler can call to other stepgroups.

    Called step-group has its own failure handler.

    Can StopStepGroup the called step-group. The outer/parent failure handler
    does NOT have a stop, so will still raise error.
    """
    pipename = (
        'tests/pipelines/errors/'
        'fail-handler-call-from-handler-nest-fail-handler')
    test_pipe_runner.assert_pipeline_raises(pipename,
                                            AssertionError,
                                            'assert False evaluated to False.',
                                            ['A', 'B', 'C', 'D', 'E', 'F'])


def test_fail_handler_call_from_handler_nest_fail_handler_stop():
    """Failure handler can call to other stepgroups and still stop.

    Called step-group has its own failure handler.

    Can StopStepGroup the called step-group. The outer/parent failure handler
    DOES have a stop too, so will not raise error.
    """
    pipename = ('tests/pipelines/errors/'
                'fail-handler-call-from-handler-nest-fail-handler-stop')
    test_pipe_runner.assert_pipeline_notify_output_is(
        pipename,
        ['A', 'B', 'C', 'D', 'E', 'F'])


def test_fail_handler_jump():
    """Failure handler can jump to other stepgroups and still raise.

    Even with the jump, still in error context, so without a Stop instruction,
    will quit reporting failure.
    """
    pipename = 'tests/pipelines/errors/fail-handler-jump'
    test_pipe_runner.assert_pipeline_raises(pipename,
                                            AssertionError,
                                            'assert False evaluated to False.',
                                            ['A', 'B', 'C'])


def test_fail_handler_jump_stop_outside():
    """Failure handler can jump to other stepgroups and still stop.

    Stop Pipeline in jumped to group stops entire pipeline without error.
    """
    pipename = 'tests/pipelines/errors/fail-handler-jump-stop-outside'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename,
                                                      ['A', 'B', 'C'])
# endregion failure handler
