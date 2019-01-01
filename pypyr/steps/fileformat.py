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

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormat missing in context.
        pypyr.errors.KeyInContextHasNoValueError: in or out exists but is None.

    """
    logger.debug("started")
    deprecated(context)

    StreamRewriterStep(__name__, 'fileFormat', context).run_step()

    logger.debug("done")


def deprecated(context):
    """Create new style in params from deprecated."""
    if 'fileFormatIn' in context:
        context.assert_keys_have_values(__name__,
                                        'fileFormatIn',
                                        'fileFormatOut')

        context['fileFormat'] = {'in': context['fileFormatIn'],
                                 'out': context['fileFormatOut']}

        logger.warning("fileFormatIn and fileFormatOut "
                       "are deprecated. They will stop working upon the next "
                       "major release. Use the new context key fileFormat "
                       "instead. It's a lot better, promise! For the moment "
                       "pypyr is creating the new fileFormat key for you "
                       "under the hood.")
