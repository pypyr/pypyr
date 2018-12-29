"""yaml handling functions."""
import ruamel.yaml as yamler
from pypyr.context import Context
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

    yaml_loader = get_yaml_parser_safe()

    for representer in tag_representers:
        yaml_loader.register_class(representer)

    pipeline_definition = yaml_loader.load(file)
    return pipeline_definition


def get_yaml_parser_safe():
    """Create the safe yaml parser object with this factory method.

    The safe yaml parser does NOT resolve unknown tags.

    Returns:
        ruamel.yaml.YAML object with safe loader

    """
    return yamler.YAML(typ='safe', pure=True)


def get_yaml_parser_roundtrip():
    """Create the yaml parser object with this factory method.

    The round-trip parser preserves:
    - comments
    - block style and key ordering are kept, so you can diff the round-tripped
      source
    - flow style sequences ( ‘a: b, c, d’) (based on request and test by
      Anthony Sottile)
    - anchor names that are hand-crafted (i.e. not of the form``idNNN``)
    - merges in dictionaries are preserved

    Returns:
        ruamel.yaml.YAML object with round-trip loader

    """
    yaml_writer = yamler.YAML(typ='rt', pure=True)
    # if this isn't here the yaml doesn't format nicely indented for humans
    yaml_writer.indent(mapping=2, sequence=4, offset=2)
    return yaml_writer


def get_yaml_parser_roundtrip_for_context():
    """Create a yaml parser that can serialize the pypyr Context.

    Create yaml parser with get_yaml_parser_roundtrip, adding Context.
    This allows the yaml parser to serialize the pypyr Context.
    """
    yaml_writer = get_yaml_parser_roundtrip()

    # Context is a dict data structure, so can just use a dict representer
    yaml_writer.Representer.add_representer(
        Context,
        yamler.representer.RoundTripRepresenter.represent_dict)

    return yaml_writer
