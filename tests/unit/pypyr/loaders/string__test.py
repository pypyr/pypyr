"""pypyr.loaders.string unit tests."""
from unittest.mock import patch

import pypyr.loaders.string as string_loader
from pypyr.pipedef import PipelineBody, PipelineDefinition, PipelineStringInfo


@patch("ruamel.yaml.YAML.load", return_value={})
def test_get_pipeline_definition(mocked_yaml):
    """Unit test get_pipeline_definition."""
    pipeline = "pipeline"

    pipeline_def = string_loader.get_pipeline_definition(pipeline, None)

    mocked_yaml.assert_called_once_with(pipeline)
    expected_pipeline_def = PipelineDefinition(
        PipelineBody.from_mapping({}),
        PipelineStringInfo(loader="pypyr.loaders.string"),
    )

    assert pipeline_def == expected_pipeline_def
