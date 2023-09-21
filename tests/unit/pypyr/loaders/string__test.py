"""pypyr.loaders.string unit tests."""
from unittest.mock import patch

import pypyr.loaders.string as string_loader
from pypyr.models import Pipeline
from pypyr.pipedef import PipelineDefinition, PipelineFileInfo


@patch("ruamel.yaml.YAML.load", return_value={})
def test_get_pipeline_definition(mocked_yaml):
    """Unit test get_pipeline_definition."""
    pipeline = "pipeline"

    pipeline_def = string_loader.get_pipeline_definition(pipeline, None)

    mocked_yaml.assert_called_once_with(pipeline)
    expected_pipeline_def = PipelineDefinition(
        Pipeline(),
        PipelineFileInfo(
            pipeline_name="",
            loader="pypyr.loaders.string",
            parent=None,
            path=None,
        ),
    )
    assert pipeline_def == expected_pipeline_def
