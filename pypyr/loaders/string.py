"""Load pipelines from string."""
import logging

from pypyr.pipedef import PipelineDefinition, PipelineFileInfo
from pypyr.yaml import get_pipeline

logger = logging.getLogger(__name__)


def get_pipeline_definition(pipeline_name, parent=None):
    """
    Receives a pipeline as string, parses it and returns a PipelineDefinition.

    Args:
        pipeline_name (str): pipeline as string.
        parent (Path-like): ignored

    Returns:
        PipelineDefinition describing the pipeline.
            The dict parsed from the pipeline is in its .pipeline property.
    """
    logger.debug("starting")

    pipeline = get_pipeline(pipeline_name)
    info = PipelineFileInfo(
        pipeline_name="", parent=parent, loader=__name__, path=None
    )
    definition = PipelineDefinition(pipeline=pipeline, info=info)

    logger.debug("pipeline:", definition.pipeline)
    logger.debug("done")

    return definition
