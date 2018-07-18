"""pypyr step that loads json file into context."""
import json
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Loads a json file into the pypyr context.

    json parsed from the file will be merged into the pypyr context. This will
    overwrite existing values if the same keys are already in there.
    I.e if file json has {'eggs' : 'boiled'} and context {'eggs': 'fried'}
    already exists, returned context['eggs'] will be 'boiled'.

    The json should not be an array [] on the top level, but rather an Object.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - fetchJsonPath. path-like. Path to file on disk.

    Returns:
        None. updates context arg.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fetchJsonPath missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fetchJsonPath exists but is
                                                None.
    """
    logger.debug("started")
    context.assert_key_has_value(key='fetchJsonPath', caller=__name__)

    file_path = context.get_formatted('fetchJsonPath')

    logger.debug(f"attempting to open file: {file_path}")
    with open(file_path) as json_file:
        payload = json.load(json_file)

    logger.debug("json file loaded. Merging into pypyr context. . .")
    context.update(payload)
    logger.info(f"json file merged into pypyr context. Count: {len(payload)}")
    logger.debug("done")
