"""Step that stops current pipeline."""
import logging
from pypyr.errors import StopPipeline

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Stop current pipeline."""
    logger.debug("started")

    logger.info("StopPipeline: stopping pipeline...")
    raise StopPipeline("pypyr.steps.stoppipeline stopped current pipeline")
