"""yamlfile.py unit tests."""
from unittest.mock import patch

import pytest

import pypyr.parser.yamlfile


def test_yaml_file_open_fails_on_arbitrary_string():
    """Non path-y input string should fail."""
    with pytest.raises(FileNotFoundError):
        pypyr.parser.yamlfile.get_parsed_context('value 1,value 2, value3')


def test_yaml_file_open_fails_on_empty_string():
    """Non path-y input string should fail."""
    with pytest.raises(AssertionError):
        pypyr.parser.yamlfile.get_parsed_context(None)


def test_yaml_pass(fs):
    """Relative path to yaml should succeed."""
    in_path = './tests/testfiles/dict.yaml'
    fs.create_file(in_path, contents="""key1: value1
key2: value2
key3: value3
key4:
  k41: k41value
  k42:
    - k42list1
    - k42list2
    - k42list3
  k43: True
  k44: 77
key5:
  - k5list1
  - k5list2
""")
    context = pypyr.parser.yamlfile.get_parsed_context([in_path])

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


@patch('pypyr.config.config.default_encoding', new='utf-16')
def test_yaml_pass_with_encoding(fs):
    """Relative path to yaml should succeed."""
    in_path = './tests/testfiles/dict.yaml'
    fs.create_file(in_path, contents="""key1: value1
key2: value2
key3: value3
key4:
  k41: k41value
  k42:
    - k42list1
    - k42list2
    - k42list3
  k43: True
  k44: 77
key5:
  - k5list1
  - k5list2
""", encoding='utf-16')

    context = pypyr.parser.yamlfile.get_parsed_context([in_path])

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


def test_list_yaml_fails(fs):
    """Yaml describing a list rather than a dict should fail."""
    in_path = './tests/testfiles/list.yaml'
    fs.create_file(in_path, contents="""- listitem1
- listitem2
  - listitem2.1
  - listitem2.2
- listitem3
""")
    with pytest.raises(TypeError):
        pypyr.parser.yamlfile.get_parsed_context([in_path])
