"""pypyr.loaders.string integration tests."""
from textwrap import dedent

from pypyr import pipelinerunner
from pypyr.dsl import Step
from pypyr.loaders.string import get_pipeline_definition
from pypyr.pipedef import PipelineBody


def test_get_pipeline_definition():
    """Test get_pipeline_definition."""
    pipeline = dedent(
        """\
        steps:
          - name: pypyr.steps.echo
            in:
              echoMe: 'testing'
        """
    )

    definition = get_pipeline_definition(pipeline, None)

    assert definition.pipeline == PipelineBody(
        step_groups={
            'steps': [
                Step(
                    name='pypyr.steps.echo',
                    in_parameters={'echoMe': 'testing'},
                    line_col=5,
                    line_no=2,
                )
            ]
        }
    )


def test_run_with_custom_runner():
    """Test run with custom string loader."""
    pipeline = dedent(
        """\
        steps:
          - name: pypyr.steps.set
            in:
              set:
                test: 1
        """
    )

    context = pipelinerunner.run(
        pipeline_name=pipeline, loader="pypyr.loaders.string"
    )

    assert context["test"] == 1
