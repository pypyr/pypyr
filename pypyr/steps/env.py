"""Step that gets, sets and unsets env vars."""
import os
import logging
from pypyr.errors import KeyNotInContextError

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Get, set, unset $ENVs.

    Context is a dictionary or dictionary-like. context is mandatory.

    Input context is:
        env:
            get: {dict}
            set: {dict}
            unset: [list]

    At least one of env's sub-keys (get, set or unset) must exist.

    This step will run whatever combination of Get, Set and Unset you specify.
    Regardless of combination, execution order is Get, Set, Unset.
    """
    logger.debug("started")
    assert context, f"context must have value for {__name__}"
    deprecated(context)

    context.assert_key_has_value('env', __name__)

    found_get = env_get(context)
    found_set = env_set(context)
    found_unset = env_unset(context)

    # at least 1 of envGet, envSet or envUnset must exist in context
    if not (found_get or found_set or found_unset):
        raise KeyNotInContextError(
            "context must contain any combination of "
            "env['get'], env['set'] or env['unset'] for "
            f"{__name__}")

    logger.debug("done")


def env_get(context):
    """Get $ENVs into the pypyr context.

    Context is a dictionary or dictionary-like. context is mandatory.

    context['env']['get'] must exist. It's a dictionary.
    Values are the names of the $ENVs to write to the pypyr context.
    Keys are the pypyr context item to which to write the $ENV values.

    For example, say input context is:
        key1: value1
        key2: value2
        pypyrCurrentDir: value3
        env:
            get:
                pypyrUser: USER
                pypyrCurrentDir: PWD

    This will result in context:
        key1: value1
        key2: value2
        key3: value3
        pypyrUser: <<value of $USER here>>
        pypyrCurrentDir: <<value of $PWD here, not value3>>
    """
    get = context['env'].get('get', None)

    exists = False
    if get:
        logger.debug("start")

        for k, v in get.items():
            logger.debug(f"setting context {k} to $ENV {v}")
            context[k] = os.environ[v]

        logger.info(f"saved {len(get)} $ENVs to context.")
        exists = True

        logger.debug("done")
    return exists


def env_set(context):
    """Set $ENVs to specified string. from the pypyr context.

    Args:
        context: is dictionary-like. context is mandatory.
                 context['env']['set'] must exist. It's a dictionary.
                 Values are strings to write to $ENV.
                 Keys are the names of the $ENV values to which to write.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        env:
            set:
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
    env_set = context['env'].get('set', None)

    exists = False
    if env_set:
        logger.debug("started")

        for k, v in env_set.items():
            logger.debug(f"setting ${k} to context[{v}]")
            os.environ[k] = context.get_formatted_string(v)

        logger.info(f"set {len(env_set)} $ENVs from context.")
        exists = True

        logger.debug("done")

    return exists


def env_unset(context):
    """Unset $ENVs.

    Context is a dictionary or dictionary-like. context is mandatory.

    context['env']['unset'] must exist. It's a list.
    List items are the names of the $ENV values to unset.

    For example, say input context is:
        key1: value1
        key2: value2
        key3: value3
        env:
            unset:
                MYVAR1
                MYVAR2

    This will result in the following $ENVs being unset:
    $MYVAR1
    $MYVAR2
    """
    unset = context['env'].get('unset', None)

    exists = False
    if unset:
        logger.debug("started")

        for env_var_name in unset:
            logger.debug(f"unsetting ${env_var_name}")
            try:
                del os.environ[env_var_name]
            except KeyError:
                # If user is trying to get rid of the $ENV, if it doesn't
                # exist, no real point in throwing up an error that the thing
                # you're trying to be rid off isn't there anyway.
                logger.debug(
                    f"${env_var_name} doesn't exist anyway. As you were.")

        logger.info(f"unset {len(unset)} $ENVs.")
        exists = True

        logger.debug("done")
    return exists


def deprecated(context):
    """Handle deprecated context input."""
    env = context.get('env', None)

    get_info, set_info, unset_info = context.keys_of_type_exist(
        ('envGet', dict),
        ('envSet', dict),
        ('envUnset', list)
    )

    found_at_least_one = (get_info.key_in_context or set_info.key_in_context
                          or unset_info.key_in_context)

    if found_at_least_one:
        env = context['env'] = {}
    else:
        return

    if get_info.key_in_context and get_info.is_expected_type:
        env['get'] = context[get_info.key]

    if set_info.key_in_context and set_info.is_expected_type:
        env['set'] = context[set_info.key]

    if unset_info.key_in_context and unset_info.is_expected_type:
        env['unset'] = context[unset_info.key]

    logger.warning("envGet, envSet and envUnset are deprecated. They will "
                   "stop working upon the next major release. "
                   "Use the new context key env instead. It's a lot "
                   "better, promise! For the moment pypyr is creating the "
                   "new env key for you under the hood.")
