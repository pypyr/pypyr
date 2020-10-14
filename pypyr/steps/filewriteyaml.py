"""pypyr step that writes payload out to a yaml file."""
import os
import logging
from pypyr.utils.asserts import assert_key_has_value
import pypyr.yaml

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Write payload out to yaml file.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileWriteYaml
                    - path. mandatory. path-like. Write output file to
                      here. Will create directories in path for you.
                    - payload. optional. Write this to output file. If not
                      specified, output entire context.

    Returns:
        None.

    Raises:
        pypyr.errors.KeyNotInContextError: fileWriteYaml or
            fileWriteYaml['path'] missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileWriteYaml or
            fileWriteYaml['path'] exists but is None.

    """
    logger.debug("started")
    context.assert_key_has_value('fileWriteYaml', __name__)

    input_context = context.get_formatted('fileWriteYaml')
    assert_key_has_value(obj=input_context,
                         key='path',
                         caller=__name__,
                         parent='fileWriteYaml')
    out_path = input_context['path']
    # doing it like this to safeguard against accidentally dumping all context
    # with potentially sensitive values in it to disk if payload exists but is
    # None.
    is_payload_specified = 'payload' in input_context

    yaml_writer = pypyr.yaml.get_yaml_parser_roundtrip_for_context()

    logger.debug("opening destination file for writing: %s", out_path)
    os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
    with open(out_path, 'w') as outfile:
        if is_payload_specified:
            payload = input_context['payload']
        else:
            payload = context.get_formatted_value(context)

        yaml_writer.dump(payload, outfile)

    logger.info("formatted context content and wrote to %s", out_path)
    logger.debug("done")
