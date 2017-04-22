"""Context parser that returns a dictionary from a local yaml file."""

from collections.abc import MutableMapping
import pypyr.log.logger
import ruamel.yaml as yaml

# use pypyr logger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


def get_parsed_context(context_arg):
    """Parse input context string and returns context as dictionary."""
    assert context_arg, ("pipeline must be invoked with --context set. For "
                         "this yaml parser you're looking for something "
                         "like --context './myyamlfile.yaml'")
    logger.debug("starting")
    logger.debug(f"attempting to open file: {context_arg}")
    with open(context_arg) as yaml_file:
        payload = yaml.safe_load(yaml_file)

    logger.debug(f"yaml file parsed. Count: {len(payload)}")

    if not isinstance(payload, MutableMapping):
        raise TypeError("yaml input should describe a dictionary at the top "
                        "level. You should have something like "
                        "\n'key1: value1'\n key2: value2'\n"
                        "in the yaml top-level, not \n'- value1\n - value2'")

    logger.debug("done")
    return payload
