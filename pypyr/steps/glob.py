"""pypyr step that gets paths from a glob."""
import logging
from pypyr.errors import KeyInContextHasNoValueError
import pypyr.utils.filesystem

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """pypyr step gets paths from a glob input.

    Do note that this will returns files AND directories that match the glob.

    No tilde expansion is done, but *, ?, and character ranges expressed with
    [] will be correctly matched.

    Escape all special characters ('?', '*' and '['). For a literal match, wrap
    the meta-characters in brackets. For example, '[?]' matches the character
    '?'.

    If passing in an iterable of paths, will expand matches for each path in
    the iterable. The function will return all the matches for each path
    glob expression combined into a single list.

    If no matches found, writes empty list [] to globOut.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key is mandatory:
                - glob. str or list. Single path, or list of paths.

    All inputs support pypyr formatting expressions.

    Returns:
        None. updates context ['globOut'] with list of resolved paths as
              strings.

    """
    logger.debug("started")
    context.assert_key_has_value(key='glob', caller=__name__)

    paths = context.get_formatted('glob')
    if isinstance(paths, list):
        if not paths or any(not p for p in paths):
            raise KeyInContextHasNoValueError("The glob list has an empty str")
        in_count = len(paths)
    else:
        if not paths:
            raise KeyInContextHasNoValueError("The glob path is an empty str")
        in_count = 1

    context['globOut'] = pypyr.utils.filesystem.get_glob(paths)

    logger.info("glob checked %s globs and saved "
                "%s paths to globOut", in_count, len(context['globOut']))
    logger.debug("done")
