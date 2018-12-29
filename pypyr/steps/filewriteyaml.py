"""pypyr step that writes payload out to a yaml file."""
import os
import logging
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
    context.assert_child_key_has_value('fileWriteYaml', 'path', __name__)

    out_path = context.get_formatted_string(context['fileWriteYaml']['path'])
    # doing it like this to safeguard against accidentally dumping all context
    # with potentially sensitive values in it to disk if payload exists but is
    # None.
    is_payload_specified = 'payload' in context['fileWriteYaml']

    yaml_writer = pypyr.yaml.get_yaml_parser_roundtrip_for_context()

    logger.debug(f"opening destination file for writing: {out_path}")
    os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
    with open(out_path, 'w') as outfile:
        if is_payload_specified:
            payload = context['fileWriteYaml']['payload']
            formatted_iterable = context.get_formatted_iterable(payload)
        else:
            formatted_iterable = context.get_formatted_iterable(context)

        yaml_writer.dump(formatted_iterable, outfile)

    logger.info(f"formatted context content and wrote to {out_path}")
    logger.debug("done")
