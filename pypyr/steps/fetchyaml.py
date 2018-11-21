"""pypyr step that loads yaml file into context."""
from collections.abc import MutableMapping
import logging
import ruamel.yaml as yaml

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Load a yaml file into the pypyr context.

    Yaml parsed from the file will be merged into the pypyr context. This will
    overwrite existing values if the same keys are already in there.
    I.e if file yaml has {'eggs' : 'boiled'} and context {'eggs': 'fried'}
    already exists, returned context['eggs'] will be 'boiled'.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - fetchYamlPath. path-like. Path to file on disk.
                - fetchYamlKey. string. If exists, write yaml to this context
                                key. Else yaml writes to context root.

    All inputs support formatting expressions.

    Returns:
        None. updates context arg.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fetchYamlPath missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fetchYamlPath exists but is
                                                  None.

    """
    logger.debug("started")
    context.assert_key_has_value(key='fetchYamlPath', caller=__name__)

    destination_key_expression = context.get('fetchYamlKey', None)

    file_path = context.get_formatted('fetchYamlPath')

    logger.debug(f"attempting to open file: {file_path}")
    with open(file_path) as yaml_file:
        yaml_loader = yaml.YAML(typ='safe', pure=True)
        payload = yaml_loader.load(yaml_file)

    if destination_key_expression:
        destination_key = context.get_formatted_iterable(
            destination_key_expression)
        logger.debug(f"yaml file loaded. Writing to context {destination_key}")
        context[destination_key] = payload
    else:
        if not isinstance(payload, MutableMapping):
            raise TypeError(
                "yaml input should describe a dictionary at the top "
                "level when fetchYamlKey isn't specified. You should have "
                "something like \n'key1: value1'\n key2: value2'\n"
                "in the yaml top-level, not \n'- value1\n - value2'")

        logger.debug("yaml file loaded. Merging into pypyr context. . .")
        context.update(payload)

    logger.info(f"yaml file written into pypyr context. Count: {len(payload)}")
    logger.debug("done")
