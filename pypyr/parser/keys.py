"""Context parser that returns a dictionary from input args.

Takes input args and returns a dictionary where each element
becomes the key, with value to true.

So cli input like this "ham eggs bacon", will yield:
{'ham': True, 'eggs': True, 'bacon': True}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input context string and returns context as dictionary."""
    logger.debug("starting")
    if not args:
        logger.debug("pipeline invoked without context arg set. For "
                     "this keys parser you're looking for something "
                     "like: pypyr pipelinename spam eggs \n"
                     "or: pypyr pipelinename spam."
                     )
        return None

    # for each arg, project (element-name, true)
    return dict((element, True) for element in args)
