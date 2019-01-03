"""json.py unit tests."""
import pypyr.parser.json
import json
import pytest


def test_json_cant_parse_from_arbitrary_string():
    """Comma delimited input string should fail."""
    with pytest.raises(json.JSONDecodeError):
        pypyr.parser.json.get_parsed_context('value 1,value 2, value3')


def test_json_parser_empty_string_empty_dict():
    """Empty inpout string creates empty dict."""
    out = pypyr.parser.json.get_parsed_context(None)
    assert not out
