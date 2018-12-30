"""Context parser that returns a dictionary from a key-value pair string.

Takes a comma delimited key=value pair string and returns a dictionary where
each pair becomes a dictionary element, as children of a dict key argDict.

Don't have spaces between commas unless your really mean it. "k1=v1, k2=v2"
will result in a context key name of ' k2' not 'k2'.

So a string like this "pig=ham,hen=eggs,yummypig=bacon", will yield:
{'argDict': {'pig': 'ham', 'hen': ''eggs', 'yummypig': 'bacon'}}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    if not context_arg:
        logger.debug("pipeline invoked without context arg set. For this "
                     "keyvaluepairstokey parser you can use something "
                     "like: "
                     "pypyr pipelinename 'key1=value1,key2=value2'.")
        return {'argDict': None}

    logger.debug("starting")
    # for each comma-delimited element, project key=value
    return {'argDict':
            dict(element.split('=') for element in context_arg.split(','))}
