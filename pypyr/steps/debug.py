"""pypyr step that pretty prints debug information to console.

Dumps the pypyr context to stdout. This may assist in debugging when trying to
see what values are what.

All inputs are optional. This means you can run debug in a pipeline just with
- pypyr.steps.debug
In this case it will dump the entire context as is without applying formatting.

Debug supports the following optional inputs:
debug:
    keys: str for a single key name to dump. Or a list of key names to dump.
    format: Boolean, defaults False. Applies formatting expressions on output.

"""
import json
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Print debug info to console.

    context is a dictionary or dictionary-like.

    If you use pypyr.steps.debug as a simple step (i.e you do NOT specify the
    debug input context), it will just dump the entire context to stdout.

    Configure the debug step with the following optional context item:
        debug:
            keys: str (for single key) or list (of str keys). Only dump the
                  specified keys.
            format: bool. Defaults False. Applies formatting expressions on
                    dump.
    """
    logger.debug("started")

    debug = context.get('debug', None)

    if debug:
        keys = debug.get('keys', None)
        format = debug.get('format', False)

        if keys:
            logger.debug(f"Writing to output: {keys}")
            if isinstance(keys, str):
                payload = {keys: context[keys]}
            else:
                payload = {k: context[k] for k in keys}
        else:
            logger.debug(
                "No keys specified. Writing entire context to output.")
            payload = context

        if format:
            payload = context.get_formatted_iterable(payload)
    else:
        payload = context

    logger.info(f'\n{json.dumps(payload, indent=2, ensure_ascii=False)}')

    logger.debug("done")
