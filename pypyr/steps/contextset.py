"""pypyr step that sets context values from already existing context values.

This is handy if you need to prepare certain keys in context where a next step
might need a specific key. If you already have the value in context, you can
create a new key (or update existing key) with that value.

So let's say you already have context['currentKey'] = 'eggs'.
If you run newKey: currentKey, you'll end up with context['newKey'] == 'eggs'
"""
import pypyr.log.logger

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Create new context keys from already existing context keys.

    Context is a dictionary or dictionary-like.
    context['contextSet'] must exist. It's a dictionary.
    Will iterate context['contextSet'] and save the values as new keys to the
    context.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        contextSet:
            key2: key1
            key4: key3

    This will result in return context:
        key1: value1
        key2: value1
        key3: value3
        key4: value3
    """
    logger.debug("started")
    context.assert_key_has_value(key='contextSet', caller=__name__)

    for k, v in context['contextSet'].items():
        logger.debug(f"setting context {k} to value from context {v}")
        context[k] = context[v]

    logger.debug("done")
