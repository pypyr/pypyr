"""pypyr step that wipes the entire context."""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Wipe the entire context, including the pyimport namespace.

    Args:
        Context is a dictionary or dictionary-like.
        Does not require any specific keys in context.
    """
    logger.debug("started")

    context.clear()
    context.pystring_globals_clear()

    logger.info("context & py imports wiped. New context size: %s",
                len(context))

    logger.debug("done")
