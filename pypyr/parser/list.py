"""Context parser that returns a list from input arguments.

Takes input args (i.e separated by spaces on cli) and returns a list named
argList.

So a string like this "ham eggs bacon", will yield context:
{ 'argList': ['ham', 'eggs', 'bacon']}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input context args and returns context as dictionary."""
    logger.debug("starting")
    if not args:
        logger.debug("pipeline invoked without context arg set. For "
                     "this list parser you're looking for something like:\n"
                     "pypyr pipelinename spam eggs\n"
                     "OR: pypyr pipelinename spam."
                     )
        return {'argList': []}

    # the list that's parsed from the input args is named argList
    return dict({'argList': args})
