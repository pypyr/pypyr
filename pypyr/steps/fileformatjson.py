"""pypyr step that parses json file for string substitutions, writes output."""
import os
import json
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parses input json file and substitutes {tokens} from context.

    Loads json into memory to do parsing, so be aware of big files.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileFormatJsonIn. mandatory. path-like.
                  Path to source file on disk.
                - fileFormatJsonOut. mandatory. path-like. Write output file to
                  here. Will create directories in path for you.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormatJsonIn or
            fileFormatJsonOut missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileFormatJsonIn or
            fileFormatJsonOut exists but is None.
    """
    logger.debug("started")
    context.assert_keys_have_values(__name__,
                                    'fileFormatJsonIn',
                                    'fileFormatJsonOut')

    in_path = context.get_formatted('fileFormatJsonIn')
    out_path = context.get_formatted('fileFormatJsonOut')

    logger.debug(f"opening json source file: {in_path}")
    with open(in_path) as infile:
        payload = json.load(infile)

    logger.debug(f"opening destination file for writing: {out_path}")
    os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
    with open(out_path, 'w') as outfile:
        formatted_iterable = context.get_formatted_iterable(payload)
        json.dump(formatted_iterable, outfile, indent=4, ensure_ascii=False)

    logger.info(f"Read {in_path}, formatted contents and wrote to {out_path}")
    logger.debug("done")
