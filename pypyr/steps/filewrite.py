"""pypyr step that writes payload out to a file."""
import logging
from pathlib import Path

from pypyr.utils.asserts import assert_key_exists, assert_key_is_truthy

logger = logging.getLogger(__name__)


def run_step(context):
    """Write payload to file.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileWrite
                    - path. mandatory. path-like. Write output file to
                      here. Will create directories in path for you.
                    - payload. optional. Write this value to output file.
                    - append. boolean. Default False. Set to True to append to
                      file if it exists already. If False will overwrite
                      existing file.
                    - binary. boolean. Default False. Set to True to write file
                      content as bytes in binary mode. Set both append & binary
                      True to append to binary file.

    Returns:
        None.

    Raises:
        pypyr.errors.KeyNotInContextError: fileWrite or
            fileWrite['path'] missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileWrite or
            fileWrite['path'] exists but is None/Empty.

    """
    logger.debug("started")
    context.assert_key_has_value('fileWrite', __name__)

    file_write = context.get_formatted('fileWrite')
    assert_key_is_truthy(obj=file_write,
                         key='path',
                         caller=__name__,
                         parent='fileWrite')

    assert_key_exists(obj=file_write,
                      key='payload',
                      caller=__name__,
                      parent='fileWrite')

    path = Path(file_write['path'])
    is_append = file_write.get('append', False)
    is_binary = file_write.get('binary', False)

    if is_binary:
        mode = 'ab' if is_append else 'wb'
        payload = file_write['payload']
    else:
        mode = 'a' if is_append else 'w'
        # if payload is str already, str(payload) is payload (same obj id)
        payload = str(file_write['payload'])

    logger.debug("opening destination file for writing: %s", path)

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode) as file:
        file.write(payload)

    logger.info("formatted context & wrote to %s", path)
    logger.debug("done")
