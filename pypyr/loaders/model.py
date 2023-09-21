import logging
from typing import Optional, List

from attrs import define

from pypyr.pipedef import PipelineFileInfo, PipelineDefinition

logger = logging.getLogger(__name__)


@define
class Step:
    name: str
    comment: Optional[str] = None
    description: Optional[str] = None
    foreach: Optional[list] = None
    in_: Optional[dict] = None
    onError: Optional[str] = None  # TODO
    retry: Optional[dict] = None  # TODO
    run: bool = True
    skip: bool = False
    swallow: bool = False
    while_: Optional[dict] = None  # TODO


@define
class Pipeline:
    context_parser: Optional[str] = None
    steps: Optional[List[Step]] = None  # TODO
    on_success: Optional[List[Step]] = None  # TODO
    on_failure: Optional[List[Step]] = None  # TODO


def get_pipeline_definition(pipeline_name, parent=None):
    """
    Receives a pipeline and returns a PipelineDefinition.

    Args:
        pipeline_name (Pipeline): pipeline.
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
