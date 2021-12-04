"""pypyr step that parses a json string to context."""
from collections.abc import Mapping
import json
import logging
from pypyr.errors import KeyInContextHasNoValueError
from pypyr.utils.asserts import assert_key_exists


logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input string into Context as an object.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - jsonParse
                    - json. string or formatting expression evaluating to a
                      string of json.
                    - key. string. If exists, write json structure to this
                      context key. Else json writes to context root.

    Returns:
        None.

    Raises:
        pypyr.errors.KeyNotInContextError: jsonParse or jsonParse.json missing
                                           in context.
        pypyr.errors.KeyInContextHasNoValueError: jsonParse.json exists but is
                                                  empty.

    """
    logger.debug("started")
    context.assert_key_has_value('jsonParse', __name__)

    input_context = context.get_formatted('jsonParse')
    assert_key_exists(obj=input_context,
                      key='json',
                      caller=__name__,
                      parent='jsonParse')

    destination_key = input_context.get('key', None)

    json_string = input_context['json']
    if not json_string:
        raise KeyInContextHasNoValueError(
            'jsonParse.json exists but is empty. It should be a valid json '
            'string for pypyr.steps.jsonparse. For example: '
            '\'{"key1": "value1", "key2": "value2"}\'')

    payload = json.loads(json_string)

    if destination_key:
        logger.debug("json string parsed. Writing to context %s",
                     destination_key)
        context[destination_key] = payload
    else:
        if not isinstance(payload, Mapping):
            raise TypeError(
                'json input should describe an object at the top '
                'level when jsonParse.key isn\'t specified. You should have '
                'something like \'{"key1": "value1", "key2": "value2"}\' '
                'in the json top-level, not ["value1", "value2"]')

        logger.debug("json string parsed. Merging into pypyr context at %s...",
                     destination_key)
        context.update(payload)

    logger.info("json string parsed into pypyr context.")

    logger.debug("done")
