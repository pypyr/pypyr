"""pypyr step that parses yaml for string substitutions, writes output."""
import logging
from pypyr.utils.filesystem import ObjectRewriter, YamlRepresenter

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input yaml file and substitute {tokens} from context.

    Loads yaml into memory to do parsing, so be aware of big files.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileFormatYamlIn. mandatory. path-like.
                  Path to source file on disk.
                - fileFormatYamlOut. mandatory. path-like. Write output file to
                  here. Will create directories in path for you.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormatYamlIn or
            fileFormatYamlOut missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileFormatYamlIn or
            fileFormatYamlOut exists but is None.

    """
    logger.debug("started")
    context.assert_keys_have_values(__name__,
                                    'fileFormatYamlIn',
                                    'fileFormatYamlOut')

    in_path = context.get_formatted('fileFormatYamlIn')
    out_path = context.get_formatted(
        'fileFormatYamlOut') if 'fileFormatYamlOut' in context else None

    rewriter = ObjectRewriter(context.get_formatted_iterable,
                              YamlRepresenter())
    rewriter.files_in_to_out(in_path=in_path, out_path=out_path)

    logger.debug("done")
