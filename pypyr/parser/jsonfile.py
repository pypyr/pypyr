"""Context parser that returns a dictionary from a local json file."""

import logging
import json

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse args as path to a json file and returns context as dictionary."""
    assert args, ("pipeline must be invoked with context arg set. For "
                  "this json parser you're looking for something "
                  "like: "
                  "pypyr pipelinename './myjsonfile.json'")
    logger.debug("starting")
    path = ' '.join(args)
    # open the json file on disk so that you can initialize the dictionary
    logger.debug("attempting to open file: %s", path)
    with open(path) as json_file:
        payload = json.load(json_file)

    logger.debug("json file loaded into context. Count: %d", len(payload))
    logger.debug("done")
    return payload
