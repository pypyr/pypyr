"""Step that gets $ENVs, using a default value if the $ENV doesn't exist."""
import os
import logging
from pypyr.errors import ContextError, KeyNotInContextError

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Get $ENVs, allowing a default if not found.

    Set context properties from environment variables, and specify a default
    if the environment variable is not found.

    This differs from pypyr.steps.env get, which raises an error if attempting
    to read an $ENV that doesn't exist.

    Args:
        context. mandatory. Context is a pypyr Context.

    Input context is:
        envGet:
            - env: 'envvarnamehere'
              key: 'savetocontexthere'
              default: 'save this to key if env doesnt exist'

    'env' is the bare environment variable name, do not put the $ in front of
    it.

    Will process as many env/key/default pairs as exist in the list under
    envGet.

    Returns:
        None.

    Raises:
        ContextError: envGet is not a list of dicts.
        KeyNotInContextError: envGet env or key doesn't exist.

    """
    logger.debug("started")
    assert context, f"context must have value for {__name__}"

    context.assert_key_has_value('envGet', __name__)

    get_items = context.get_formatted('envGet')
    # allow a list OR a single getenv dict
    if isinstance(context['envGet'], dict):
        get_items = [get_items]

    get_count = 0

    for get_me in get_items:
        (env, key, has_default, default) = get_args(get_me)

        logger.debug("setting context %s to $ENV %s", key, env)

        if env in os.environ:
            context[key] = os.environ[env]
            get_count += 1
        else:
            logger.debug("$ENV %s not found.", env)
            if has_default:
                logger.debug("Using default value for %s instead.", env)
                context[key] = os.environ.get(env, default)
                get_count += 1
            else:
                logger.debug(
                    "No default value for %s found. Doin' nuthin'.", env)

    logger.info("saved %s $ENVs to context.", get_count)


def get_args(get_item):
    """Parse env, key, default out of input dict.

    Args:
        get_item: dict. contains keys env/key/default

    Returns:
        (env, key, has_default, default) tuple, where
            env: str. env var name.
            key: str. save env value to this context key.
            has_default: bool. True if default specified.
            default: the value of default, if specified.

    Raises:
        ContextError: envGet is not a list of dicts.
        KeyNotInContextError: If env or key not found in get_config.

    """
    if not isinstance(get_item, dict):
        raise ContextError('envGet must contain a list of dicts.')

    env = get_item.get('env', None)

    if not env:
        raise KeyNotInContextError(
            'context envGet[env] must exist in context for envGet.')

    key = get_item.get('key', None)

    if not key:
        raise KeyNotInContextError(
            'context envGet[key] must exist in context for envGet.')

    if 'default' in get_item:
        has_default = True
        default = get_item['default']
    else:
        has_default = False
        default = None

    return (env, key, has_default, default)
