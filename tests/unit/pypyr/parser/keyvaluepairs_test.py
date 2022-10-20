"""keyvaluepairs.py unit tests."""
import pypyr.parser.keyvaluepairs


def test_kvp_args_parses_to_dict():
    """Comma delimited input kvp string should return dictionary."""
    out = pypyr.parser.keyvaluepairs.get_parsed_context(['key1=value1',
                                                         'key2=value2',
                                                         ',key3=value3'])
    assert out['key1'] == 'value1', "key1 should be value1."
    assert out['key2'] == 'value2', "key2 should be value2."
    assert out[',key3'] == 'value3', "key3 should be value3."
    assert len(out) == 3, "3 items expected"


def test_kvp_args_single_parses_to_single_entry():
    """No commas input kvp string should return dictionary with 1 item."""
    out = pypyr.parser.keyvaluepairs.get_parsed_context(['key 1=value 2 '])
    assert out['key 1'] == 'value 2 ', "key 1 isnt 'value 2 '."
    assert len(out) == 1, "1 item expected"


def test_kvp_args_single_no_equals():
    """No equals input kvp ends up as key: ''."""
    out = pypyr.parser.keyvaluepairs.get_parsed_context(
        ['key1value2,value3'])

    assert out == {'key1value2,value3': ''}


def test_kvp_args_no_equals_and_equals():
    """No equals input combined with equals key value pair."""
    out = pypyr.parser.keyvaluepairs.get_parsed_context(
        ['key1value2,value3', "key1=123"])

    assert out == {'key1value2,value3': '', 'key1': '123'}


def test_kvp_args_ignore_double_equals():
    """Ignore double equals."""
    out = pypyr.parser.keyvaluepairs.get_parsed_context(
        ['key1value2,value3', "key 1=123=45 6"])

    assert out == {'key1value2,value3': '', 'key 1': '123=45 6'}


def test_kvp_empty_args_empty_dict():
    """Empty input args should return empty dict."""
    out = pypyr.parser.keyvaluepairs.get_parsed_context(None)
    assert not out
