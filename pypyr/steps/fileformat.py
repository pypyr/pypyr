"""pypyr step that parses file for string substitutions and writes output."""
import os
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parses input file and substitutes {tokens} from context.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileFormatIn. mandatory. path-like.
                  Path to source file on disk.
                - fileFormatOut. mandatory. path-like. Write output file to
                  here. Will create directories in path for you.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormatIn or fileFormatOut
                                           missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileFormatIn or fileFormatOut
                                                  exists but is None.
    """
    logger.debug("started")
    context.assert_keys_have_values(__name__, 'fileFormatIn', 'fileFormatOut')

    in_path = context.get_formatted('fileFormatIn')
    out_path = context.get_formatted('fileFormatOut')

    logger.debug(f"opening source file: {in_path}")
    with open(in_path) as infile:
        logger.debug(f"opening destination file for writing: {out_path}")
        os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
        with open(out_path, 'w') as outfile:
            outfile.writelines(context.iter_formatted_strings(infile))

    logger.info(f"Read {in_path}, formatted and wrote to {out_path}")
    logger.debug("done")
