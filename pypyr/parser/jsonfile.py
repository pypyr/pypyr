"""Context parser that returns a dictionary from a local json file."""
from collections.abc import Mapping
import logging
import json

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse args as path to a json file and returns context as dictionary."""
    logger.debug("starting")
    if not args:
        raise AssertionError(
            "pipeline must be invoked with context arg set. For "
            "this json parser you're looking for something like:\n"
            "pypyr pipelinename ./myjsonfile.json")

    path = ' '.join(args)
    # open the json file on disk so that you can initialize the dictionary
    logger.debug("attempting to open file: %s", path)
    with open(path) as json_file:
        payload = json.load(json_file)

    if not isinstance(payload, Mapping):
        raise TypeError("json input should describe an object at the top "
                        "level. You should have something like\n"
                        "{\n\"key1\":\"value1\",\n\"key2\":\"value2\"\n}\n"
                        "at the json top-level, not an [array] or literal.")

    logger.debug("json file loaded into context. Count: %d", len(payload))
    logger.debug("done")
    return payload
