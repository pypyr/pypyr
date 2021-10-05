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
    context['set'] must exist. It's a dictionary.
    Will iterate context['set'] and save the values as new keys to the
    context.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        set:
            key2: 'aaa_{key1}_zzz'
            key4: 'bbb_{key3}_yyy'

    This will result in return context:
        key1: value1
        key2: aaa_value1_zzz
        key3: bbb_value3_yyy
        key4: value3
    """
    logger.debug("started")
    context.assert_key_has_value(key='set', caller=__name__)

    # since context ends up in globals for PyStrings, NOT doing this means
    # built-in set() masked by this dict under key 'set'.
    # A side-effect of this is that if you define "set" context in a previous
    # step and not in "in", this will wipe it from context regardless.
    set_me = context.pop('set')

    for k, v in set_me.items():
        logger.debug("setting context %s to value from context %s", k, v)
        context[context.get_formatted_value(
            k)] = context.get_formatted_value(v)

    logger.info("set %d context items.", len(set_me))

    logger.debug("done")
