"""Step that sets env vars from the pypyr context."""
import os
import pypyr.log.logger

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Set $ENVs from the pypyr context.

    Context is a dictionary or dictionary-like. context is mandatory.

    context['envSet'] must exist. It's a dictionary.
    Values are the keys of the pypyr context values to write to $ENV.
    Keys are the names of the $ENV values to which to write.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        envSet:
            MYVAR1: key1
            MYVAR2: key3

    This will result in the following $ENVs:
    $MYVAR1 = value1
    $MYVAR2 = value3

    Note that the $ENVs are not persisted system-wide, they only exist for
    pypyr sub-processes, and as such for the following steps during this pypyr
    pipeline execution. If you set an $ENV here, don't expect to see it in your
    system environment variables after the pipeline finishes running.
    """
    logger.debug("started")
    context.assert_key_has_value(key='envSet', caller=__name__)

    for k, v in context['envSet'].items():
        logger.debug(f"setting ${k} to context[{v}]")
        os.environ[k] = context[v]

    logger.debug("done")
