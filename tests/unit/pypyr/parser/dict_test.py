"""dict.py unit tests."""
import pypyr.parser.dict


def test_arg_string_parses_to_argdict():
    """Args input kvp string should return dictionary."""
    out = pypyr.parser.dict.get_parsed_context(['key1=value1',
                                                'key 2=value2',
                                                'key3=value3'])
    arg_dict = out['argDict']
    assert arg_dict
    assert arg_dict['key1'] == 'value1', "key1 should be value1."
    assert arg_dict['key 2'] == 'value2', "key2 should be value2."
    assert arg_dict['key3'] == 'value3', "key3 should be value3."
    assert len(out) == 1
    assert len(arg_dict) == 3, "3 items expected"


def test_arg_string_parses_to_single_entry_argdict():
    """Input kvp string should return dictionary with 1 item."""
    out = pypyr.parser.dict.get_parsed_context(['key 1=value 2 value3'])
    arg_dict = out['argDict']
    assert arg_dict
    assert arg_dict['key 1'] == 'value 2 value3'
    assert len(out) == 1, "1 item expected"
    assert len(arg_dict) == 1, "1 item expected"


def test_no_equals_string_parses_to_single_entry_argdict():
    """No equals input kvp parses to key=''."""
    out = pypyr.parser.dict.get_parsed_context(['key1value2,value3'])
    assert out == {'argDict': {'key1value2,value3': ''}}


def test_argdict_no_equals_combined_with_equals():
    """No equals input kvp string parses to key='' and key=value."""
    out = pypyr.parser.dict.get_parsed_context(
        ['key1value2,value3', 'key 1=value 1'])
    assert out == {'argDict': {'key1value2,value3': '',
                               'key 1': 'value 1'}}


def test_argdict_no_equals_combined_with_double_equals():
    """Ignore subsequent equals."""
    out = pypyr.parser.dict.get_parsed_context(
        ['key1value2,value3', 'key 1=value 1=123'])
    assert out == {'argDict': {'key1value2,value3': '',
                               'key 1': 'value 1=123'}}


def test_empty_string_empty_dict_argdict():
    """Empty input string should return empty argDict."""
    out = pypyr.parser.dict.get_parsed_context(None)

    assert out
    assert not out['argDict']
    assert out['argDict'] == {}
