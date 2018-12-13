"""yaml.py unit tests."""
import io
import pytest
import pypyr.yaml as pypyr_yaml


def test_get_pipeline_yaml_simple():
    """Pipeline yaml loads with simple yaml."""
    file = io.StringIO('1: 2\n2: 3')
    pipeline = pypyr_yaml.get_pipeline_yaml(file)

    assert pipeline == {1: 2, 2: 3}


def test_get_pipeline_yaml_custom_types():
    """Pipeline yaml loads with custom types."""
    file = io.StringIO('1: !sic "{12}"\n2: !py abs(-23)\n3: !sic\n4: !py')
    pipeline = pypyr_yaml.get_pipeline_yaml(file)

    assert len(pipeline) == 4
    assert pipeline[1].get_value() == '{12}'
    assert repr(pipeline[2]) == "PyString('abs(-23)')"
    assert pipeline[2].value == 'abs(-23)'
    assert pipeline[2].get_value({}) == 23
    # empty sic
    assert repr(pipeline[3]) == "SicString('')"
    assert pipeline[3].get_value({}) == ''
    # empty py
    assert repr(pipeline[4]) == "PyString('')"

    with pytest.raises(ValueError) as err:
        pipeline[4].get_value({})
        assert str(err.value) == (
            '!py string expression is empty. It must be a valid python '
            'expression instead.')
