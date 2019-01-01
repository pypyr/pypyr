"""pypyr step that parses file, does string replacement and writes output."""
import logging
from pypyr.steps.dsl.fileinoutrewriter import StreamReplacePairsRewriterStep

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input file and replace a search string.

    This also does string substitutions from context on the fileReplacePairs.
    It does this before it search & replaces the in file.

    Be careful of order. If fileReplacePairs is not an ordered collection,
    replacements could evaluate in any given order. If this is coming in from
    pipeline yaml it will be an ordered dictionary, so life is good.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileReplace
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
                    - replacePairs. mandatory. Dictionary where items are:
                      'find_string': 'replace_string'

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: Any of the required keys missing in
                                          context.
        pypyr.errors.KeyInContextHasNoValueError: Any of the required keys
                                                  exists but is None.

    """
    logger.debug("started")
    deprecated(context)
    StreamReplacePairsRewriterStep(__name__, 'fileReplace', context).run_step()

    logger.debug("done")


def deprecated(context):
    """Create new style in params from deprecated."""
    if 'fileReplaceIn' in context:
        context.assert_keys_have_values(__name__,
                                        'fileReplaceIn',
                                        'fileReplaceOut',
                                        'fileReplacePairs')

        context['fileReplace'] = {'in': context['fileReplaceIn'],
                                  'out': context['fileReplaceOut'],
                                  'replacePairs': context['fileReplacePairs']}

        logger.warning("fileReplaceIn, fileReplaceOut and fileReplacePairs "
                       "are deprecated. They will stop working upon the next "
                       "major release. Use the new context key fileReplace "
                       "instead. It's a lot better, promise! For the moment "
                       "pypyr is creating the new fileReplace key for you "
                       "under the hood.")
