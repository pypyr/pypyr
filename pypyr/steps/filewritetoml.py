"""pypyr step that writes payload out to a toml file."""
import logging
from pathlib import Path

from pypyr.errors import KeyInContextHasNoValueError
import pypyr.toml as toml
from pypyr.utils.asserts import assert_key_has_value

logger = logging.getLogger(__name__)

sentinel = object()


def run_step(context):
    """Write payload out to toml file.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileWriteToml
                    - path. mandatory. path-like. Write output file to
                      here. Will create directories in path for you.
                    - payload. optional. Write this key to output file. If not
                      specified, output entire context.

    If you do specify a payload, it cannot be None or empty.

    Returns:
        None.

    Raises:
        pypyr.errors.KeyNotInContextError: fileWriteToml or
            fileWriteToml.path missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileWriteToml or
            fileWriteToml.path exists but is None.

    """
    logger.debug("started")

    input_key_name = 'fileWriteToml'
    context.assert_key_has_value(input_key_name, __name__)

    input_context = context.get_formatted(input_key_name)
    assert_key_has_value(obj=input_context,
                         key='path',
                         caller=__name__,
                         parent=input_key_name)

    out_path = Path(input_context['path'])
    # doing it like this to safeguard against accidentally dumping all context
    # with potentially sensitive values in it to disk if payload exists but is
    # None.
    payload = input_context.get('payload', sentinel)

    if payload is sentinel:
        payload = context.get_formatted_value(context)
    else:
        if not payload:
            raise KeyInContextHasNoValueError(
                "payload must have a value to write to output TOML document.")

        payload = input_context['payload']

    logger.debug("opening destination file for writing: %s", out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    toml.write_file(out_path, payload)

    logger.info("formatted context content and wrote to %s", out_path)
    logger.debug("done")
