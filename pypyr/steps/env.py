"""Step that gets, sets and unsets env vars."""
import os
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Get, set, unset $ENVs.

    Context is a dictionary or dictionary-like. context is mandatory.

    At least one of these context keys must exist:
    context['envGet']
    context['envSet']
    context['envUnset']

    This step will run whatever combination of Get, Set and Unset you specify.
    Regardless of combination, execution order is Get, Set, Unset.
    """
    logger.debug("started")
    # at least 1 of envGet, envSet or envUnset must exist in context
    assert context, f"context must have value for {__name__}"
    get_info, set_info, unset_info = context.keys_of_type_exist(
        ('envGet', dict),
        ('envSet', dict),
        ('envUnset', list)
    )
    found_at_least_one = False

    if get_info.key_in_context and get_info.is_expected_type:
        found_at_least_one = True
        env_get(context)

    if set_info.key_in_context and set_info.is_expected_type:
        found_at_least_one = True
        env_set(context)

    if unset_info.key_in_context and unset_info.is_expected_type:
        found_at_least_one = True
        env_unset(context)

    assert found_at_least_one, ("context must contain any combination of "
                                f"envGet, envSet or envUnset for {__name__}")
    logger.debug("done")


def env_get(context):
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
    logger.debug("start")

    for k, v in context['envGet'].items():
        logger.debug(f"setting context {k} to $ENV {v}")
        context[k] = os.environ[v]

    logger.debug("done")


def env_set(context):
    """Set $ENVs to specified string. from the pypyr context.

    Args:
        context: is dictionary-like. context is mandatory.
                 context['envSet'] must exist. It's a dictionary.
                 Values are strings to write to $ENV.
                 Keys are the names of the $ENV values to which to write.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        envSet:
            MYVAR1: {key1}
            MYVAR2: before_{key3}_after
            MYVAR3: arbtexthere

    This will result in the following $ENVs:
    $MYVAR1 = value1
    $MYVAR2 = before_value3_after
    $MYVAR3 = arbtexthere

    Note that the $ENVs are not persisted system-wide, they only exist for
    pypyr sub-processes, and as such for the following steps during this pypyr
    pipeline execution. If you set an $ENV here, don't expect to see it in your
    system environment variables after the pipeline finishes running.
    """
    logger.debug("started")

    for k, v in context['envSet'].items():
        logger.debug(f"setting ${k} to context[{v}]")
        os.environ[k] = context.get_formatted_string(v)

    logger.debug("done")


def env_unset(context):
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

    for env_var_name in context['envUnset']:
        logger.debug(f"unsetting ${env_var_name}")
        try:
            del os.environ[env_var_name]
        except KeyError:
            # If user is trying to get rid of the $ENV, if it doesn't exist, no
            # real point in throwing up an error that the thing you're trying
            # to be rid off isn't there anyway.
            logger.debug(f"${env_var_name} doesn't exist anyway. As you were.")

    logger.debug("done")
