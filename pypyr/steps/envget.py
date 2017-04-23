"""Step that gets env vars and set context values from them."""
import os
import pypyr.log.logger

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Get $ENVs into the pypyr context.

    Context is a dictionary or dictionary-like. context is mandatory.

    context['envGet'] must exist. It's a dictionary.
    Values are the names of the $ENVs to write to the pypyr context.
    Keys are the pypyr context item to which to write the $ENV values.

    For example, say input context is:
        key1: value1
        key2: value2
        pypyrCurrentDir: value3
        envGet:
            pypyrUser: USER
            pypyrCurrentDir: PWD

    This will result in context:
        key1: value1
        key2: value2
        key3: value3
        pypyrUser: <<value of $USER here>>
        pypyrCurrentDir: <<value of $PWD here, not value3>>
    """
    logger.debug("started")
    context.assert_key_has_value(key='envGet', caller='envget')

    for k, v in context['envGet'].items():
        logger.debug(f"setting context {k} to $ENV {v}")
        context[k] = os.environ[v]

    logger.debug("done")
