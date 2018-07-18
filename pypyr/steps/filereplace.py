"""pypyr step that parses file, does string replacement and writes output."""
from functools import reduce
import os
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parses input file and replaces a search string.

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
    out_path = context.get_formatted('fileReplaceOut')

    logger.debug("Running subsitutions from context on fileReplacePairs")
    formatted_replacements = context.get_formatted_iterable(
        context['fileReplacePairs'])

    logger.debug(f"opening source file: {in_path}")
    with open(in_path) as infile:
        logger.debug(f"opening destination file for writing: {out_path}")
        os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
        with open(out_path, 'w') as outfile:
            outfile.writelines(iter_replace_strings(infile,
                                                    formatted_replacements))

    logger.info(f"Read {in_path}, replaced strings and wrote to {out_path}")
    logger.debug("done")


def iter_replace_strings(iterable_strings, replacements):
    """Generator that yields a formatted string from iterable_strings.

    Args:
        iterable_strings: Iterable containing strings. E.g a file-like object.
        replacements: Dict containing 'find_string': 'replace_string' pairs

    Returns:
        Yields formatted line.
    """
    for string in iterable_strings:
        yield reduce((lambda s, kv: s.replace(*kv)),
                     replacements.items(),
                     string)
