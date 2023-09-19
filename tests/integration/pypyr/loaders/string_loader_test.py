"""pypyr.loaders.string integration tests."""
from textwrap import dedent

from pypyr import pipelinerunner
from pypyr.loaders.string import get_pipeline_definition


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

    assert definition.pipeline == {
        "steps": [{"name": "pypyr.steps.echo", "in": {"echoMe": "testing"}}]
    }


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
