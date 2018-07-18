"""Context parser that returns a list from a comma delimited string.

Takes a comma delimited string and returns a list named argList.

So a string like this "ham,eggs,bacon", will yield context:
{ 'argList': ['ham', 'eggs', 'bacon']}
"""
import logging

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with context arg set. For "
                         "this list parser you're looking for something like: "
                         "pypyr pipelinename 'spam,eggs' "
                         "OR: pypyr pipelinename 'spam'."
                         )
    logger.debug("starting")
    # the list that's parsed from the input args is named argList
    return dict({'argList': context_arg.split(',')})
