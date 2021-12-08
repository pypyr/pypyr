"""pypyr step that parses toml file for string substitutions, writes output."""
import logging
from pypyr.steps.dsl.fileinoutrewriter import ObjectRewriterStep
from pypyr.utils.filesystem import TomlRepresenter

logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input toml file and substitute {tokens} from context.

    Loads toml into memory to do parsing, so be aware of big files.

    Args:
        context: pypyr.context.Context. Mandatory.
                - fileFormatToml
                    - in. mandatory.
                      str, path-like, or an iterable (list/tuple) of
                      strings/paths. Each str/path can be a glob, relative or
                      absolute path.
                    - out. optional. path-like.
                      Can refer to a file or a directory.
                      will create directory structure if it doesn't exist. If
                      in-path refers to >1 file (e.g it's a glob or list), out
                      path can only be a directory - it doesn't make sense to
                      write >1 file to the same single file (this is not an
                      appender.) To ensure out_path is read as a directory and
                      not a file, be sure to have the path separator (/) at the
                      end.
                      If out_path is not specified or None, will in-place edit
                      and overwrite the in-files.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormatToml or
            fileFormatToml['in'] missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileFormatToml or
            fileFormatToml['in'] exists but is None.
    """
    logger.debug("started")

    ObjectRewriterStep(__name__, 'fileFormatToml', context).run_step(
        TomlRepresenter())

    logger.debug("done")
