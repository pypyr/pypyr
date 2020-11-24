"""yaml.py unit tests."""
import io
import pytest
import ruamel.yaml as yamler
from pypyr.context import Context
import pypyr.yaml as pypyr_yaml


# region get_pipeline_yaml
def test_get_pipeline_yaml_simple():
    """Pipeline yaml loads with simple yaml."""
    file = io.StringIO('1: 2\n2: 3')
    pipeline = pypyr_yaml.get_pipeline_yaml(file)

    assert pipeline == {1: 2, 2: 3}


def test_get_pipeline_yaml_custom_types():
    """Pipeline yaml loads with custom types."""
    file = io.StringIO('1: !sic "{12}"\n2: !py abs(-23)\n3: !sic\n4: !py')
    pipeline = pypyr_yaml.get_pipeline_yaml(file)
    context = Context()

    assert len(pipeline) == 4
    assert pipeline[1].get_value() == '{12}'
    assert repr(pipeline[2]) == "PyString('abs(-23)')"
    assert pipeline[2].value == 'abs(-23)'
    assert pipeline[2].get_value(context) == 23
    # empty sic
    assert repr(pipeline[3]) == "SicString('')"
    assert pipeline[3].get_value({}) == ''
    # empty py
    assert repr(pipeline[4]) == "PyString('')"

    with pytest.raises(ValueError) as err:
        pipeline[4].get_value(context)
        assert str(err.value) == (
            '!py string expression is empty. It must be a valid python '
            'expression instead.')

# endregion get_pipeline_yaml

# region get_yaml_parser


def test_get_yaml_parser_safe():
    """Create yaml parser safe."""
    obj = pypyr_yaml.get_yaml_parser_safe()
    assert obj.typ == ['safe']
    assert obj.pure


def test_get_yaml_parser_roundtrip():
    """Create yaml parser roundtrip."""
    obj = pypyr_yaml.get_yaml_parser_roundtrip()
    assert obj.typ == ['rt']
    assert obj.pure
    assert obj.map_indent == 2
    assert obj.sequence_indent == 4
    assert obj.sequence_dash_offset == 2


def test_get_yaml_parser_roundtrip_context():
    """Create yaml parser roundtrip with Context representer."""
    obj = pypyr_yaml.get_yaml_parser_roundtrip_for_context()
    assert obj.typ == ['rt']
    assert obj.pure
    assert obj.map_indent == 2
    assert obj.sequence_indent == 4
    assert obj.sequence_dash_offset == 2
    assert obj.Representer.yaml_representers[Context] == (
        yamler.representer.RoundTripRepresenter.represent_dict)
# endregion get_yaml_parser ---------------------------------------
