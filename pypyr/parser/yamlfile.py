"""Context parser that returns a dictionary from a local yaml file."""
from collections.abc import Mapping
import logging
import ruamel.yaml as yaml

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(args):
    """Parse input as path to a yaml file, returns context as dictionary."""
    logger.debug("starting")
    if not args:
        raise AssertionError(
            "pipeline must be invoked with context arg set. For "
            "this yaml parser you're looking for something like:\n"
            "pypyr pipelinename ./myyamlfile.yaml")
    path = ' '.join(args)
    logger.debug("attempting to open file: %s", path)
    with open(path) as yaml_file:
        yaml_loader = yaml.YAML(typ='safe', pure=True)
        payload = yaml_loader.load(yaml_file)

    if not isinstance(payload, Mapping):
        raise TypeError("yaml input should describe a dictionary at the top "
                        "level. You should have something like\n"
                        "key1: value1\n key2: value2\n"
                        "in the yaml top-level, not \n- value1\n- value2")

    logger.debug("yaml file parsed. Count: %d", len(payload))

    logger.debug("done")
    return payload
