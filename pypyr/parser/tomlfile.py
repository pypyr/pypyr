"""Context parser that returns a dict-like from a toml file."""
import logging

import pypyr.toml as toml

logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input as path to a toml file, returns dict of toml contents."""
    logger.debug("starting")
    if not args:
        logger.debug("pipeline invoked without context arg set. For this toml "
                     "parser you're looking for something like: $ pypyr "
                     "pipelinename ./myfile.toml")
        return None

    path = ' '.join(args)
    logger.debug("attempting to open file: %s", path)
    payload = toml.read_file(path)

    # no special check whether top-level is mapping necessary, by spec toml
    # can only have mapping (key-value pairs or table) at top level.

    logger.debug("toml file parsed. Count: %d", len(payload))

    logger.debug("done")
    return payload
