"""Step that unsets env vars."""
import os
import pypyr.log.logger
import pypyr.validate.asserts

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Unset $ENVs.

    Context is a dictionary or dictionary-like. context is mandatory.

    context['envUnset'] must exist. It's a list.
    List items are the names of the $ENV values to unset.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        envUnset:
            MYVAR1
            MYVAR2

    This will result in the following $ENVs being unset:
    $MYVAR1
    $MYVAR2
    """
    logger.debug("started")
    pypyr.validate.asserts.key_in_context_has_value(
        context=context, key='envUnset', caller='envunset')

    for env_var_name in context['envUnset']:
        logger.debug(f"unsetting ${env_var_name}")
        del os.environ[env_var_name]

    logger.debug("done")
