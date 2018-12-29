"""pypyr step that parses file for string substitutions and writes output."""
import logging
from pypyr.utils.filesystem import StreamRewriter

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input file and substitutes {tokens} from context.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileFormatIn. mandatory. path-like.
                  Path to source file on disk.
                - fileFormatOut. optional. path-like/str. Write output file to
                  here. Will create directories in path for you. NOT LIST.

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

    out_path = context.get_formatted(
        'fileFormatOut') if 'fileFormatOut' in context else None

    rewriter = StreamRewriter(context.iter_formatted_strings)
    rewriter.files_in_to_out(in_path=in_path, out_path=out_path)

    logger.debug("done")
