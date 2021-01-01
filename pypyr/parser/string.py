"""Context parser that adds the input argument string into the pypyr context.

Takes any arbitrary string and adds it to the context dict as argString.

So a string like this "ham eggs bacon", will yield context:
{'argString': 'ham eggs bacon'}
"""
import logging

# getLogger will grab the parent logger context, so your loglevel and
# formatting will inherit correctly automatically from the pypyr core.
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input context string and returns context as dictionary."""
    logger.debug("starting")
    if not args:
        logger.debug("pipeline invoked without context arg set. For "
                     "this string parser you're looking for something "
                     "like: pypyr pipelinename spam and eggs"
                     )
        return {'argString': ''}

    # the list that's parsed from the input args is named argList
    return dict({'argString': ' '.join(args)})
