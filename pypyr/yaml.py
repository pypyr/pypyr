"""yaml handling functions."""
import ruamel.yaml as yamler
from pypyr.dsl import PyString, SicString


def get_pipeline_yaml(file):
    """Return pipeline yaml from open file object.

    Use specific custom representers to model the custom pypyr pipeline yaml
    format, to load in special literal types like py and sic strings.

    If looking to extend the pypyr pipeline syntax with special types, add
    these to the tag_representers list.

    Args:
        file: open file-like object.

    Returns:
        dict-like representation of loaded yaml.

    """
    tag_representers = [PyString, SicString]

    yaml_loader = yamler.YAML(typ='safe', pure=True)

    for representer in tag_representers:
        yaml_loader.register_class(representer)

    pipeline_definition = yaml_loader.load(file)
    return pipeline_definition
