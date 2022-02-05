"""pypyr step that loads yaml file into context."""
from collections.abc import Mapping
import logging

import ruamel.yaml as yaml

from pypyr.config import config
from pypyr.utils.asserts import assert_key_has_value

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
                - fetchYaml
                    - path. path-like. Path to file on disk.
                    - key. string. If exists, write yaml to this context key.
                      Else yaml writes to context root.
                    - encoding. string. Defaults None (platform default,
                      usually 'utf-8').

    All inputs support formatting expressions.

    Also supports a passing path as string to fetchYaml, but in this case you
    won't be able to specify a key.

    If you do not set encoding, will use the system default, which is utf-8
    for everything except windows.

    Returns:
        None. updates context arg.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fetchYamlPath missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fetchYamlPath exists but is
                                                  None.

    """
    logger.debug("started")

    context.assert_key_has_value(key='fetchYaml', caller=__name__)

    fetch_yaml_input = context.get_formatted('fetchYaml')

    if isinstance(fetch_yaml_input, str):
        file_path = fetch_yaml_input
        destination_key = None
        encoding = config.default_encoding
    else:
        assert_key_has_value(obj=fetch_yaml_input,
                             key='path',
                             caller=__name__,
                             parent='fetchYaml')
        file_path = fetch_yaml_input['path']
        destination_key = fetch_yaml_input.get('key', None)
        encoding = fetch_yaml_input.get('encoding', config.default_encoding)

    logger.debug("attempting to open file: %s", file_path)
    with open(file_path, encoding=encoding) as yaml_file:
        yaml_loader = yaml.YAML(typ='safe', pure=True)
        payload = yaml_loader.load(yaml_file)

    if destination_key:
        logger.debug("yaml file loaded. Writing to context %s",
                     destination_key)
        context[destination_key] = payload
    else:
        if not isinstance(payload, Mapping):
            raise TypeError(
                "yaml input should describe a dictionary at the top "
                "level when fetchYaml.key isn't specified. You should have "
                "something like \n'key1: value1'\n key2: value2'\n"
                "in the yaml top-level, not \n'- value1\n - value2'")

        logger.debug("yaml file loaded. Merging into pypyr context. . .")
        context.update(payload)

    logger.info("yaml file written into pypyr context. Count: %s",
                len(payload))
    logger.debug("done")
