"""pypyr step copies context values from already existing context values.

This is handy if you need to prepare certain keys in context where a next step
might need a specific key. If you already have the value in context, you can
create a new key (or update existing key) with that value.

So let's say you already have context['currentKey'] = 'eggs'.
If you run newKey: currentKey, you'll end up with context['newKey'] == 'eggs'
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Create/copy new context keys from already existing context keys.

    Context is a dictionary or dictionary-like.
    context['contextCopy'] must exist. It's a dictionary.
    Will iterate context['contextCopy'] and save the values as new keys to the
    context.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        contextCopy:
            key2: key1
            key4: key3

    This will result in return context:
        key1: value1
        key2: value1
        key3: value3
        key4: value3
    """
    logger.debug("started")
    context.assert_key_has_value(key='contextCopy', caller=__name__)

    for k, v in context['contextCopy'].items():
        logger.debug("copying context %s to value from context %s", k, v)
        context[k] = context[v]

    logger.debug("done")
