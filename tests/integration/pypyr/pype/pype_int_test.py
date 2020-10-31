"""Pype integration tests. Pipelines in ./tests/pipelines/pype."""
import tests.common.pipeline_runner as test_pipe_runner
# ------------------------- runErrors ----------------------------------------#


def test_pype_pipearg_int():
    """Pype parses pypeArg string and accessible in child."""
    pipename = 'pype/pipeargs'
    test_pipe_runner.assert_pipeline_notify_output_is(pipename, ['A',
                                                                 'B',
                                                                 'C',
                                                                 'C',
                                                                 'D'])
