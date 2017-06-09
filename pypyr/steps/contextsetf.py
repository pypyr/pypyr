"""pypyr step that sets context values from formatting expressions.

This is handy if you need to prepare certain keys in context where a next step
might need a specific key. If you already have the value in context, you can
create a new key (or update existing key) with that value.
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Set new context keys from formatting expressions with substitutions.

    Context is a dictionary or dictionary-like.
    context['contextSetf'] must exist. It's a dictionary.
    Will iterate context['contextSetf'] and save the values as new keys to the
    context.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        contextSetf:
            key2: 'aaa_{key1}_zzz'
            key4: 'bbb_{key3}_yyy'

    This will result in return context:
        key1: value1
        key2: aaa_value1_zzz
        key3: bbb_value3_yyy
        key4: value3
    """
    logger.debug("started")
    context.assert_key_has_value(key='contextSetf', caller=__name__)

    for k, v in context['contextSetf'].items():
        logger.debug(f"setting context {k} to value from context {v}")
        context[k] = context.get_formatted_iterable(v)

    logger.info(f"Set {len(context['contextSetf'])} context items.")

    logger.debug("done")
