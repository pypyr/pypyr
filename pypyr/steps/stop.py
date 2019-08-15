"""Step that stops all pypyr execution."""
import logging
from pypyr.errors import Stop

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Immediately stop all processing."""
    logger.debug("started")

    logger.info("Stop: stopping pypyr...")
    raise Stop("pypyr.steps.stop stopped pypyr execution")
