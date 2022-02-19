"""pypyr step that gets the full path to the current Python executable."""
import logging
import sys

logger = logging.getLogger(__name__)


def run_step(context):
    """Get the full path to the current Python executable.

    Args:
        Context is a dictionary or dictionary-like.
        Does not require any specific keys in context.
    """
    logger.debug("started")
    context['python'] = sys.executable
    logger.debug("done")
