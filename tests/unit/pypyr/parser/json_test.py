"""json.py unit tests."""
import pypyr.parser.json
import json
import pytest


def test_json_cant_parse_from_arbitrary_string():
    """Comma delimited input string should fail."""
    with pytest.raises(json.JSONDecodeError):
        pypyr.parser.json.get_parsed_context('value 1,value 2, value3')


def test_json_parser_empty_string_empty_dict():
    """Empty input creates empty dict."""
    out = pypyr.parser.json.get_parsed_context(None)
    assert not out


def test_json_parse_ok():
    """Valid json input parses."""
    out = pypyr.parser.json.get_parsed_context(['{', '"a": "b"', '}'])
    assert out == {'a': 'b'}


def test_json_parse_not_mapping_at_root():
    """Not mapping at root level raises."""
    with pytest.raises(TypeError) as err_info:
        pypyr.parser.json.get_parsed_context(['[1,', '2,', '3]'])

    assert str(err_info.value) == (
        "json input should describe an object at the top "
        "level. You should have something like \n"
        "{\n\"key1\":\"value1\",\n\"key2\":\"value2\"\n}\n"
        "at the json top-level, not an [array] or literal.")
