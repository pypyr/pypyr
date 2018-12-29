"""pypyr step that parses file, does string replacement and writes output."""
from functools import reduce
import logging
from pypyr.utils.filesystem import StreamRewriter

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
                - fileReplaceIn. mandatory. path-like.
                  Path to source file on disk.
                - fileReplaceOut. mandatory. path-like. Write output file to
                  here. Will create directories in path for you.
                - fileReplacePairs. mandatory. Dictionary where items are:
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
    context.assert_keys_have_values(__name__,
                                    'fileReplaceIn',
                                    'fileReplaceOut',
                                    'fileReplacePairs')

    in_path = context.get_formatted('fileReplaceIn')
    out_path = context.get_formatted(
        'fileReplaceOut') if 'fileReplaceOut' in context else None

    logger.debug("Running substitutions from context on fileReplacePairs")
    formatted_replacements = context.get_formatted_iterable(
        context['fileReplacePairs'])

    rewriter = StreamRewriter(iter_replace_strings(formatted_replacements))
    rewriter.files_in_to_out(in_path=in_path, out_path=out_path)

    logger.debug("done")


def iter_replace_strings(replacements):
    """Create a function that will use replacement pairs to process a string.

    The returned function takes an iterator and yields on each processed line.

    Args:
        replacements: Dict containing 'find_string': 'replace_string' pairs

    Returns:
        function with signature: iterator of strings = function(iterable)

    """
    def function_iter_replace_strings(iterable_strings):
        """Yield a formatted string from iterable_strings using a generator.

        Args:
            iterable_strings: Iterable containing strings. E.g a file-like
                              object.

        Returns:
            Yields formatted line.

        """
        for string in iterable_strings:
            yield reduce((lambda s, kv: s.replace(*kv)),
                         replacements.items(),
                         string)

    return function_iter_replace_strings
