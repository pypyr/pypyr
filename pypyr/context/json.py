"""Context parser that returns a dictionary from a json string."""

import pypyr.log.logger
import json

# use pypyrlogger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


def get_parsed_context(context):
    """Parse input context string and returns context as dictionary."""
    assert context, ("""pipeline must be invoked with --context set. For this "
                     "json parser you're looking for something like "
                     "--context '{"key1":"value1","key2":"value2"}'""")
    logger.debug("starting")
    # deserialize the input context string into json
    return json.loads(context)
