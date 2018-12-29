"""pypyr step that writes payload out to a json file."""
import json
import logging
import os

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


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
    context.assert_child_key_has_value('fileWriteJson', 'path', __name__)

    out_path = context.get_formatted_string(context['fileWriteJson']['path'])
    # doing it like this to safeguard against accidentally dumping all context
    # with potentially sensitive values in it to disk if payload exists but is
    # None.
    is_payload_specified = 'payload' in context['fileWriteJson']

    logger.debug(f"opening destination file for writing: {out_path}")
    os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
    with open(out_path, 'w') as outfile:
        if is_payload_specified:
            payload = context['fileWriteJson']['payload']
            formatted_iterable = context.get_formatted_iterable(payload)
        else:
            formatted_iterable = context.get_formatted_iterable(context)

        json.dump(formatted_iterable, outfile, indent=2, ensure_ascii=False)

    logger.info(f"formatted context content and wrote to {out_path}")
    logger.debug("done")
