"""json.py unit tests."""
import pypyrcli.context.json
import json
import pytest


def test_json_cant_parse_from_arbitrary_string():
    """Comma delimited input string should fail."""
    with pytest.raises(json.JSONDecodeError):
        pypyrcli.context.json.get_parsed_context('value 1,value 2, value3')
