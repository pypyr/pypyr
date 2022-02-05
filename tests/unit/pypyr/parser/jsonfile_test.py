"""jsonfile.py unit tests."""
from unittest.mock import patch

import pytest

import pypyr.parser.jsonfile


def test_json_file_open_fails_on_arbitrary_string():
    """Non path-y input string should fail."""
    with pytest.raises(FileNotFoundError):
        pypyr.parser.jsonfile.get_parsed_context('value 1,value 2, value3')


def test_json_file_open_fails_on_empty_string():
    """Non path-y input string should fail."""
    with pytest.raises(AssertionError):
        pypyr.parser.jsonfile.get_parsed_context(None)


def test_json_pass(fs):
    """Relative path to json should succeed."""
    in_path = './tests/testfiles/test.json'
    fs.create_file(in_path, contents="""{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
""")
    context = pypyr.parser.jsonfile.get_parsed_context([in_path])

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context["key2"] == "value2", "key2 should be value2"


@patch('pypyr.config.config.default_encoding', new='utf-16')
def test_json_pass_with_encoding(fs):
    """Relative path to json should succeed with encoding."""
    in_path = './tests/testfiles/test.json'
    fs.create_file(in_path, contents="""{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
""", encoding='utf-16')

    context = pypyr.parser.jsonfile.get_parsed_context([in_path])

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context["key2"] == "value2", "key2 should be value2"


def test_json_parse_not_mapping_at_root(fs):
    """Not mapping at root level raises."""
    in_path = './tests/testfiles/singleliteral.json'
    fs.create_file(in_path, contents='123')
    with pytest.raises(TypeError) as err_info:
        pypyr.parser.jsonfile.get_parsed_context([in_path])

    assert str(err_info.value) == (
        "json input should describe an object at the top "
        "level. You should have something like\n"
        "{\n\"key1\":\"value1\",\n\"key2\":\"value2\"\n}\n"
        "at the json top-level, not an [array] or literal.")
