"""pypyr step that clears context values.

This is handy if you run the same step multiple times in a pipeline and you
don't want the previously assigned context settings for that step to impact the
next iteration.
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Remove specified keys from context.

    Args:
        Context is a dictionary or dictionary-like.
        context['contextClear'] must exist. It's a dictionary.
        Will iterate context['contextClear'] and remove those keys from
        context.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        key4: value4
        contextClear:
            - key2
            - key4
            - contextClear

    This will result in return context:
        key1: value1
        key3: value3
    """
    logger.debug("started")
    context.assert_key_has_value(key='contextClear', caller=__name__)

    for k in context['contextClear']:
        logger.debug(f"removing {k} from context")
        # slightly unorthodox pop returning None means you don't get a KeyError
        # if key doesn't exist
        context.pop(k, None)
        logger.info(f"removed {k} from context")

    logger.debug("done")
