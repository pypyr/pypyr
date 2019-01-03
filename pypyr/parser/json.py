"""Context parser that returns a dictionary from a json string."""

import logging
import json

# use pypyrlogger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    if not context_arg:
        logger.debug("pipeline invoked without context arg set. For "
                     "this json parser you're looking for something "
                     "like: "
                     "pypyr pipelinename '{\"key1\":\"value1\","
                     "\"key2\":\"value2\"}'")
        return None

    logger.debug("starting")
    # deserialize the input context string into json
    return json.loads(context_arg)
