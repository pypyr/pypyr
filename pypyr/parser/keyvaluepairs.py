"""Context parser that returns a dictionary from a key-value pair string.

Takes list of key=value pair string and returns a dictionary where
each pair becomes a dictionary element.

Don't have spaces in your values unless your really mean it. "k1=v1 ' k2'=v2"
will result in a context key name of ' k2' not 'k2'.

So cli input like this "pig=ham hen=eggs yummypig=bacon", will yield:
{'pig': 'ham', 'hen': ''eggs', 'yummypig': 'bacon'}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input context args and returns context as dictionary."""
    if not args:
        logger.debug("pipeline invoked without context arg set. For "
                     "this keyvaluepairs parser you're looking for "
                     "something like:\n"
                     "pypyr pipelinename key1=value1 key2=value2")
        return None

    logger.debug("starting")
    # for each arg, project key=value
    return dict(element.split('=') for element in args)
