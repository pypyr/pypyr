"""Context parser that returns a dictionary from a json string."""
from collections.abc import Mapping
import json
import logging

logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input context args and returns context as dictionary."""
    logger.debug("starting")
    if not args:
        logger.debug("pipeline invoked without context arg set. For "
                     "this json parser you're looking for something "
                     "like: "
                     "pypyr pipelinename '{\"key1\":\"value1\","
                     "\"key2\":\"value2\"}'")
        return None

    # deserialize the input context string into json
    payload = json.loads(' '.join(args))

    if not isinstance(payload, Mapping):
        raise TypeError("json input should describe an object at the top "
                        "level. You should have something like \n"
                        "{\n\"key1\":\"value1\",\n\"key2\":\"value2\"\n}\n"
                        "at the json top-level, not an [array] or literal.")

    return payload
