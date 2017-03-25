"""commas.py unit tests."""
import pypyrcli.context.commas
import pytest


def test_comma_string_parses_to_dict():
    """Comma delimited input string should return dictionary."""
    out = pypyrcli.context.commas.get_parsed_context('value 1,value 2, value3')
    assert out['value 1'], "value 1 should be True"
    assert out['value 2'], "value 2 should be True"
    assert len(out) == 3, "3 items expected"


def test_no_commas_string_parses_to_single_entry():
    """No commas input string should return dictionary with 1 item."""
    out = pypyrcli.context.commas.get_parsed_context('value 1 value 2 value3')
    assert out['value 1 value 2 value3'], "value 1 should be True"
    assert len(out) == 1, "1 item expected"


def test_empty_string_throw():
    """Empty input string should throw assert error."""
    with pytest.raises(AssertionError):
        pypyrcli.context.commas.get_parsed_context(None)
