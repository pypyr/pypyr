"""pypyr step that reads a file into context."""
import logging
from pypyr.utils.asserts import assert_keys_are_truthy

logger = logging.getLogger(__name__)


def run_step(context):
    """Load a file into context.

    Open file at path as text using locale.getpreferredencoding().
    Open file at path as binary bytes if binary=True.

    Save file payload to key in context.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - fileRead
                    - path. path-like. Path to file on disk.
                    - key. string. Write file payload to this context key.
                    - binary. boolean. Default False. Set to True to read file
                      content as bytes in binary mode.

    All inputs support formatting expressions.

    Returns:
        None. mutates context arg.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileRead.path or fileRead.key
                                           missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileRead.path or fileRead.key
                                                  exists but is empty.

    """
    logger.debug("started")

    context.assert_key_has_value(key='fileRead', caller=__name__)

    file_read = context.get_formatted('fileRead')

    assert_keys_are_truthy(obj=file_read,
                           keys=('path', 'key'),
                           caller=__name__,
                           parent='fileRead')

    file_path = file_read['path']
    destination_key = file_read['key']
    mode = 'rb' if file_read.get('binary', False) else 'r'

    logger.debug("attempting to open file with mode '%s': %s", mode, file_path)

    with open(file_path, mode) as file:
        payload = file.read()

    context[destination_key] = payload

    logger.info("file read into pypyr context at key: %s", destination_key)
    logger.debug("done")
