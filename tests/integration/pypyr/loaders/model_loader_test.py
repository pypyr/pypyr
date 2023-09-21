"""pypyr.loaders.model integration tests."""

from pypyr import pipelinerunner
from pypyr.loaders.model import Pipeline, Step, get_pipeline_definition


def test_get_pipeline_definition():
    """Test get_pipeline_definition."""
    pipeline = Pipeline(
        steps=[
            Step(
                name="pypyr.steps.echo",
                in_={"echoMe": "testing"},
            )
        ]
    )

    definition = get_pipeline_definition(pipeline, None)

    assert definition.pipeline == pipeline


def test_run_with_custom_runner():
    """Test run with custom model loader."""
    pipeline = Pipeline(
        steps=[
            Step(
                name="pypyr.steps.set",
                in_={"set": {"test": 1}},
            )
        ]
    )

    context = pipelinerunner.run(
        pipeline_name=pipeline, loader="pypyr.loaders.model"
    )

    assert context["test"] == 1
