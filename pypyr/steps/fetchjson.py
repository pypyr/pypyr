"""pypyr step that loads json file into context."""
from collections.abc import MutableMapping
import json
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Load a json file into the pypyr context.

    json parsed from the file will be merged into the pypyr context. This will
    overwrite existing values if the same keys are already in there.
    I.e if file json has {'eggs' : 'boiled'} and context {'eggs': 'fried'}
    already exists, returned context['eggs'] will be 'boiled'.

    The json should not be an array [] on the top level, but rather an Object.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - fetchJson
                    - path. path-like. Path to file on disk.
                    - key. string. If exists, write json structure to this
                      context key. Else json writes to context root.

    Also supports a passing path as string to fetchJson, but in this case you
    won't be able to specify a key.

    All inputs support formatting expressions.

    Returns:
        None. updates context arg.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fetchJson.path missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fetchJson.path exists but is
                                                  None.

    """
    logger.debug("started")

    context.assert_key_has_value(key='fetchJson', caller=__name__)

    fetch_json_input = context.get_formatted('fetchJson')

    if isinstance(fetch_json_input, str):
        file_path = fetch_json_input
        destination_key_expression = None
    else:
        context.assert_child_key_has_value(parent='fetchJson',
                                           child='path',
                                           caller=__name__)
        file_path = fetch_json_input['path']
        destination_key_expression = fetch_json_input.get('key', None)

    logger.debug("attempting to open file: %s", file_path)
    with open(file_path) as json_file:
        payload = json.load(json_file)

    if destination_key_expression:
        destination_key = context.get_formatted_iterable(
            destination_key_expression)
        logger.debug("json file loaded. Writing to context %s",
                     destination_key)
        context[destination_key] = payload
    else:
        if not isinstance(payload, MutableMapping):
            raise TypeError(
                'json input should describe an object at the top '
                'level when fetchJsonKey isn\'t specified. You should have '
                'something like {"key1": "value1", "key2": "value2"} '
                'in the json top-level, not ["value1", "value2"]')

        logger.debug("json file loaded. Merging into pypyr context. . .")
        context.update(payload)

    logger.info("json file written into pypyr context. Count: %s",
                len(payload))
    logger.debug("done")
