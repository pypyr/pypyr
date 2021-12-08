"""pypyr step that writes payload out to a json file."""
import json
import logging
from pathlib import Path

from pypyr.utils.asserts import assert_key_has_value

logger = logging.getLogger(__name__)

sentinel = object()


def run_step(context):
    """Write payload out to json file.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileWriteJson
                    - path. mandatory. path-like. Write output file to
                      here. Will create directories in path for you.
                    - payload. optional. Write this key to output file. If not
                      specified, output entire context.

    Returns:
        None.

    Raises:
        pypyr.errors.KeyNotInContextError: fileWriteJson or
            fileWriteJson['path'] missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileWriteJson or
            fileWriteJson['path'] exists but is None.

    """
    logger.debug("started")
    context.assert_key_has_value('fileWriteJson', __name__)

    input_context = context.get_formatted('fileWriteJson')
    assert_key_has_value(obj=input_context,
                         key='path',
                         caller=__name__,
                         parent='fileWriteJson')

    out_path = Path(input_context['path'])
    # doing it like this to safeguard against accidentally dumping all context
    # with potentially sensitive values in it to disk if payload exists but is
    # None.
    payload = input_context.get('payload', sentinel)

    logger.debug("opening destination file for writing: %s", out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if payload is sentinel:
        payload = context.get_formatted_value(context)
    else:
        payload = input_context['payload']

    with open(out_path, 'w') as outfile:
        json.dump(payload, outfile,
                  indent=2, ensure_ascii=False)

    logger.info("formatted context content and wrote to %s", out_path)
    logger.debug("done")
