"""pypyr step that parses json file for string substitutions, writes output."""
import logging
from pypyr.utils.filesystem import ObjectRewriter, JsonRepresenter

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input json file and substitute {tokens} from context.

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

    out_path = context.get_formatted(
        'fileFormatJsonOut') if 'fileFormatJsonOut' in context else None

    rewriter = ObjectRewriter(context.get_formatted_iterable,
                              JsonRepresenter())
    rewriter.files_in_to_out(in_path=in_path, out_path=out_path)

    logger.debug("done")
