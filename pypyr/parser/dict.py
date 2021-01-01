"""Context parser that returns a dictionary from a key-value pair string.

Takes multiple input arguments, where each args is a key=value pair string and
returns a dictionary where each pair becomes a dictionary element, as children
of a dict key argDict.

Don't have spaces in your values unless you really meant it. "k1=v1, ' k2'=v2"
will result in a context key name of ' k2' not 'k2'.

So a argument input string like this "pig=ham hen=eggs yummypig=bacon", will
yield:
{'argDict': {'pig': 'ham', 'hen': ''eggs', 'yummypig': 'bacon'}}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input context args and returns context as dictionary."""
    logger.debug("starting")
    if not args:
        logger.debug("pipeline invoked without context arg set. For this "
                     "dict parser you can use something "
                     "like:\n"
                     "pypyr pipelinename key1=value1 key2=value2")
        return {'argDict': {}}

    # for each input argument, project key=value
    return {'argDict':
            dict(element.split('=') for element in args)}
