import logging

from pypyr.pipedef import PipelineDefinition, PipelineFileInfo

logger = logging.getLogger(__name__)


# TODO: rename pipeline_name to something else
def get_pipeline_definition(pipeline_name, parent=None):
    """
    Receives a pipeline and returns a PipelineDefinition.

    Args:
        pipeline_name (pypyr.models.Pipeline): pipeline.
        parent (Path-like): ignored

    Returns:
        PipelineDefinition describing the pipeline.
    """
    logger.debug("starting")

    info = PipelineFileInfo(
        pipeline_name="", parent=parent, loader=__name__, path=None
    )
    definition = PipelineDefinition(pipeline=pipeline_name, info=info)

    logger.debug("pipeline.", definition.pipeline)
    logger.debug("done")

    return definition
