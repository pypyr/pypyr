"""pypyr step that parses file for string substitutions and writes output."""
import logging
from pypyr.steps.dsl.fileinoutrewriter import StreamRewriterStep

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input file and substitutes {tokens} from context.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileFormat
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
                    - encoding. string. In & out both use this encoding.
                        Defaults None (platform default, usually 'utf-8').
                    - encodingIn. str. Read in files with this encoding.
                        Default to value for 'encoding'.
                    - encodingOut. str. Write out files with this encoding.
                        Default to value for 'encoding'.

    If you do not set encoding, will use the system default, which is utf-8
    for everything except windows.

    Set 'encoding' to override system default for both in & out. Use encodingIn
    and encodingOut instead when you want different encodings for reading in
    and writing out.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormat missing in context.
        pypyr.errors.KeyInContextHasNoValueError: in or out exists but is None.

    """
    logger.debug("started")

    StreamRewriterStep(__name__, 'fileFormat', context).run_step()

    logger.debug("done")
