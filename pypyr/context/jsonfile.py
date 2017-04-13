"""Context parser that returns a dictionary from a local json file."""

import pypyr.log.logger
import json

# use pypyr logger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with --context set. For "
                         "this json parser you're looking for something "
                         "like --context './myjsonfile.json'")
    logger.debug("starting")
    # open the json file on disk so that you can initialize the dictionary
    logger.debug(f"attempting to open file: {context_arg}")
    with open(context_arg) as json_file:
        payload = json.load(json_file)

    logger.debug(f"json file loaded into context. Count: {len(payload)}")
    logger.debug("done")
    return payload
