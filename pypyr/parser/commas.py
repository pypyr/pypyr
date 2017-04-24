"""Context parser that returns a dictionary from a comma delimited string.

Takes a comma delimited string and returns a dictionary where each element
becomes the key, with value to true.

So a string like this "ham,eggs,bacon", will yield:
{'ham': True, 'eggs': True, 'bacon': True}
"""
import pypyr.log.logger

# use pypyr logger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with --context set. For "
                         "this commastolist parser you're looking for "
                         "something like--context 'spam,eggs' "
                         "or --context 'spam'.")
    logger.debug("starting")
    # for each comma-delimited element, project (element-name, true)
    return dict((element, True) for element in context_arg.split(','))
