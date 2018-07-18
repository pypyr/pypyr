"""Context parser that returns a dictionary from a local yaml file."""

from collections.abc import MutableMapping
import logging
import ruamel.yaml as yaml

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with context arg set. For "
                         "this yaml parser you're looking for something "
                         "like: "
                         "pypyr pipelinename './myyamlfile.yaml'")
    logger.debug("starting")
    logger.debug(f"attempting to open file: {context_arg}")
    with open(context_arg) as yaml_file:
        yaml_loader = yaml.YAML(typ='safe', pure=True)
        payload = yaml_loader.load(yaml_file)

    logger.debug(f"yaml file parsed. Count: {len(payload)}")

    if not isinstance(payload, MutableMapping):
        raise TypeError("yaml input should describe a dictionary at the top "
                        "level. You should have something like "
                        "\n'key1: value1'\n key2: value2'\n"
                        "in the yaml top-level, not \n'- value1\n - value2'")

    logger.debug("done")
    return payload
