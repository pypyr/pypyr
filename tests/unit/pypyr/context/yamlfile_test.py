"""yamlfile.py unit tests."""
import pypyr.parser.yamlfile
import pytest


def test_yaml_file_open_fails_on_arbitrary_string():
    """Non path-y input string should fail."""
    with pytest.raises(FileNotFoundError):
        pypyr.parser.yamlfile.get_parsed_context('value 1,value 2, value3')


def test_yaml_file_open_fails_on_empty_string():
    """Non path-y input string should fail."""
    with pytest.raises(AssertionError):
        pypyr.parser.yamlfile.get_parsed_context(None)


def test_yaml_pass():
    """Relative path to yaml should succeed"""
    context = pypyr.parser.yamlfile.get_parsed_context(
        './tests/testfiles/dict.yaml')

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


def test_list_yaml_fails():
    """Yaml describing a list rather than a dict should fail."""
    with pytest.raises(TypeError):
        pypyr.parser.yamlfile.get_parsed_context(
            './tests/testfiles/list.yaml')
