"""pypyr step that loads toml file into context."""
import logging

import pypyr.toml as toml
from pypyr.utils.asserts import assert_key_has_value

logger = logging.getLogger(__name__)


def run_step(context):
    """Load a toml file into the pypyr context.

    toml parsed from the file will be merged into the pypyr context. This will
    overwrite existing values if the same keys are already in there.
    I.e if file toml has
    eggs = "boiled"
    and context {'eggs': 'fried'} already exists, returned context['eggs'] will
    be 'boiled'.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - fetchToml
                    - path. path-like. Path to file on disk.
                    - key. string. If exists, write toml structure to this
                      context key. Else toml writes to context root.

    Also supports passing a path as string to fetchToml, but in this case you
    won't be able to specify a key.

    All inputs support formatting expressions.

    Returns:
        None. updates context arg.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fetchToml.path missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fetchToml.path exists but is
                                                  None.

    """
    logger.debug("started")

    context.assert_key_has_value(key='fetchToml', caller=__name__)

    fetch_toml_input = context.get_formatted('fetchToml')

    if isinstance(fetch_toml_input, str):
        file_path = fetch_toml_input
        destination_key = None
    else:
        assert_key_has_value(obj=fetch_toml_input,
                             key='path',
                             caller=__name__,
                             parent='fetchToml')
        file_path = fetch_toml_input['path']
        destination_key = fetch_toml_input.get('key', None)

    logger.debug("attempting to open file: %s", file_path)

    payload = toml.read_file(file_path)

    if destination_key:
        logger.debug("toml file loaded. Writing to context %s",
                     destination_key)
        context[destination_key] = payload
    else:
        # toml by definition has Mapping on top level, no need to check,
        logger.debug("toml file loaded. Merging into pypyr context...")
        context.update(payload)

    logger.info("toml file written into pypyr context. Count: %s",
                len(payload))
    logger.debug("done")
