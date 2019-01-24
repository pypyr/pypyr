"""pypyr step that checks if a file or directory path exists."""
import logging
from pypyr.errors import KeyInContextHasNoValueError
import pypyr.utils.filesystem

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """pypyr step that checks if a file or directory path exists.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - pathsToCheck. str/path-like or list of str/paths.
                                Path to file on disk to check.

    All inputs support formatting expressions. Supports globs.

    This step creates pathCheckOut in context, containing the results of the
    path check operation.

    pathCheckOut:
        'inpath':
            exists: true # bool. True if path exists.
            count: 0 # int. Number of files found for in path.
            found: ['path1', 'path2'] # list of strings. Paths of files found.

    [count] is 0 if no files found. If you specified a single input
    path to check and it exists, it's going to be 1. If you specified multiple
    in paths or a glob expression that found more than 1 result, well, take a
    guess.

    [found] is a list of all the paths found for the [inpath]. If you passed
    in a glob or globs, will contain the globs found for [inpath].

    This means you can do an existence evaluation like this in a formatting
    expression: '{pathCheckOut[inpathhere][exists]}'

    Returns:
        None. updates context arg.

    Raises:
        pypyr.errors.KeyNotInContextError: pathExists missing in context.
        pypyr.errors.KeyInContextHasNoValueError: pathCheck exists but is None.

    """
    logger.debug("started")
    context.assert_key_has_value(key='pathCheck', caller=__name__)

    paths_to_check = context['pathCheck']

    if not paths_to_check:
        raise KeyInContextHasNoValueError("context['pathCheck'] must have a "
                                          f"value for {__name__}.")

    # pathsToCheck can be a string or a list in case there are multiple paths
    if isinstance(paths_to_check, list):
        check_me = paths_to_check
    else:
        # assuming it's a str/path at this point
        check_me = [paths_to_check]

    out = {}
    total_found = 0

    for path in check_me:
        logger.debug(f"checking path: {path}")
        formatted_path = context.get_formatted_string(path)
        found_paths = pypyr.utils.filesystem.get_glob(formatted_path)
        no_of_paths = len(found_paths)
        out[path] = {
            'exists': no_of_paths > 0,
            'count': no_of_paths,
            'found': found_paths
        }
        total_found = total_found + no_of_paths

    context['pathCheckOut'] = out

    logger.info(f'checked {len(out)} path(s) and found {total_found}')
    logger.debug("done")
