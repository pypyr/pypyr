"""Step that stops current step-group."""
import logging
from pypyr.errors import StopStepGroup

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Stop current step-group."""
    logger.debug("started")

    logger.info("StopStepGroup: stopping step-group...")
    raise StopStepGroup("pypyr.steps.stopstepgroup stopped current step-group")
