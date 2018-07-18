"""Context parser that returns a dictionary from a key-value pair string.

Takes a comma delimited key=value pair string and returns a dictionary where
each pair becomes a dictionary element.

Don't have spaces between commas unless your really mean it. "k1=v1, k2=v2"
will result in a context key name of ' k2' not 'k2'.

So a string like this "pig=ham,hen=eggs,yummypig=bacon", will yield:
{'pig': 'ham', 'hen': ''eggs', 'yummypig': 'bacon'}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with context arg set. For "
                         "this keyvaluepairs parser you're looking for "
                         "something like: "
                         "pypyr pipelinename 'key1=value1,key2=value2'.")
    logger.debug("starting")
    # for each comma-delimited element, project key=value
    return dict(element.split('=') for element in context_arg.split(','))
