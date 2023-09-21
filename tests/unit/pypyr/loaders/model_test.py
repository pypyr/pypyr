"""pypyr.loaders.model unit tests."""
from pypyr.loaders.model import get_pipeline_definition
from pypyr.models import Pipeline
from pypyr.pipedef import PipelineDefinition, PipelineFileInfo


def test_get_pipeline_definition():
    """Unit test get_pipeline_definition."""
    pipeline = Pipeline()

    pipeline_def = get_pipeline_definition(pipeline, None)

    expected_pipeline_def = PipelineDefinition(
        pipeline,
        PipelineFileInfo(
            pipeline_name="",
            loader="pypyr.loaders.model",
            parent=None,
            path=None,
        ),
    )
    assert pipeline_def == expected_pipeline_def
