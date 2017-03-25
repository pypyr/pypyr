"""keyvaluepairs.py unit tests."""
import pypyrcli.context.keyvaluepairs
import pytest


def test_comma_string_parses_to_dict():
    """Comma delimited input kvp string should return dictionary."""
    out = pypyrcli.context.keyvaluepairs.get_parsed_context('key1=value1'
                                                            ',key2=value2'
                                                            ',key3=value3')
    assert out['key1'] == 'value1', "key1 should be value1."
    assert out['key2'] == 'value2', "key2 should be value2."
    assert out['key3'] == 'value3', "key3 should be value3."
    assert len(out) == 3, "3 items expected"


def test_no_commas_string_parses_to_single_entry():
    """No commas input kvp string should return dictionary with 1 item."""
    out = pypyrcli.context.keyvaluepairs.get_parsed_context('key 1=value 2 '
                                                            'value3')
    assert out['key 1'] == 'value 2 value3', "key 1 isnt 'value 2 value3'."
    assert len(out) == 1, "1 item expected"


def test_no_equals_string_parses_to_single_entry():
    """No equals input kvp string fails with ValueError."""
    with pytest.raises(ValueError):
        pypyrcli.context.keyvaluepairs.get_parsed_context(
            'key1value2,value3')


def test_empty_string_throw():
    """Empty input string should throw assert error."""
    with pytest.raises(AssertionError):
        pypyrcli.context.keyvaluepairs.get_parsed_context(None)
