"""Context parser that returns a dictionary from a key-value pair string.

Takes a comma delimited key=value pair string and returns a dictionary where
each pair becomes a dictionary element.

So a string like this "pig=ham,hen=eggs,yummypig=bacon", will yield:
{'pig': 'ham', 'hen': ''eggs', 'yummypig': 'bacon'}
"""
import pypyrcli.log.logger

# use pypyr logger to ensure loglevel is set correctly
logger = pypyrcli.log.logger.get_logger(__name__)


def get_parsed_context(context):
    """Parse input context string and returns context as dictionary."""
    assert context, ("pipeline must be invoked with --context set. For this "
                     "keyvaluepairs parser you're looking for something like "
                     "--context 'key1=value1,key2=value2'.")
    logger.debug("starting")
    # for each comma-delimited element, project key=value
    return dict(element.split('=') for element in context.split(','))
