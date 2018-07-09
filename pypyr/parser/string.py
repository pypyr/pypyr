"""Context parser that adds the input argument string into the pypyr context.

Takes any arbitrary string and adds it to the context dict as argString.

So a string like this "ham eggs bacon", will yield context:
{'argString': 'ham eggs bacon'}
"""
import logging

# getLogger will grab the parent logger context, so your loglevel and
# formatting will inherit correctly automatically from the pypyr core.
logger = logging.getLogger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with context arg set. For "
                         "this string parser you're looking for something "
                         "like: pypyr pipelinename 'spam and eggs'."
                         )
    logger.debug("starting")
    # the list that's parsed from the input args is named argList
    return dict({'argString': context_arg})
