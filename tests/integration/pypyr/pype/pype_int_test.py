"""Pype integration tests. Pipelines in ./tests/pipelines/pype."""
from pypyr.pipelinerunner import run as pipeline_run
import tests.common.pipeline_runner as test_pipe_runner


def test_pype_pipearg_int():
    """Pype parses pypeArg string and accessible in child."""
    pipename = 'tests/pipelines/pype/pipeargs'

    # this one doesn't work well with checking context out because
    # it works with pipelines that don't inherit parent scope.
    # thus catch notify output instead.
    test_pipe_runner.assert_pipeline_notify_output_is(pipename, ['A',
                                                                 'B',
                                                                 'C',
                                                                 'C',
                                                                 'D'])


def test_pype_err_int():
    """Pype calls handles error with pipeline_name correctly."""
    pipename = 'tests/pipelines/pype/pipeerr'
    out = pipeline_run(pipename)

    assert out['out'] == ['A', 'B', 'C']


def test_pype_pyimport():
    """Pype while passing pyimports to child."""
    pipename = 'tests/pipelines/pype/pyimport/parent'
    out = pipeline_run(pipename)

    assert out['out'] == ['A', 'B', 'C', 'D']


def test_pype_child_dir_relative_to_parent():
    """Child pipeline & custom steps location relative to parent."""
    pipename = 'tests/pipelines/pype/relativenesting/rootpipe'
    out = pipeline_run(pipename)

    assert out['out'] == ['A', 'B', 'C', 'D']


def test_pype_relative_pipes():
    """Sequence of relative names to nested sub-dirs same pipe diff levels."""
    pipename = 'tests/pipelines/pype/relative-pipes/pipe-a'
    out = pipeline_run(pipename)

    assert out['out'] == ['A', 'B', 'C', 'D', 'D']
