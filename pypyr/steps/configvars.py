"""pypyr step gets vars from config and writes these into context."""
import logging

from pypyr.config import config

logger = logging.getLogger(__name__)


def run_step(context):
    """Write vars from config into context.

    Args:
        Context is a dictionary or dictionary-like.

    Returns: None
    """
    logger.debug("started")

    if config.vars:
        context.update(config.vars)
        logger.debug(
            f"written {len(config.vars)} variables from config.vars into "
            "context.")
    else:
        logger.debug(
            "config.vars is empty, so there is nothing to write to context.")

    logger.debug("done")
