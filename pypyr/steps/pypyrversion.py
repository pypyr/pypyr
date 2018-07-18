"""Step that echos pypyr version."""
import logging
import pypyr.version

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Outputs pypyr version in format 'pypyr x.y.z python a.b.c'"""
    logger.debug("started")

    logger.info(f"pypyr version is: {pypyr.version.get_version()}")

    logger.debug("done")
