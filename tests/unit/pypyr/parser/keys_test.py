"""keys.py unit tests."""
import pypyr.parser.keys


def test_keys_args_parses_to_dict():
    """Args should return dictionary."""
    out = pypyr.parser.keys.get_parsed_context(['value 1',
                                                'value 2',
                                                'value3'])
    assert out['value 1'], "value 1 should be True"
    assert out['value 2'], "value 2 should be True"
    assert out['value3'], "value 3 should be True"
    assert len(out) == 3, "3 items expected"


def test_no_commas_string_parses_to_single_entry():
    """No commas input string should return dictionary with 1 item."""
    out = pypyr.parser.keys.get_parsed_context(['value 1 value 2 value3'])
    assert out['value 1 value 2 value3'], "value 1 should be True"
    assert len(out) == 1, "1 item expected"


def test_empty_string_empty_dict():
    """Empty input string should return empty dict."""
    out = pypyr.parser.keys.get_parsed_context(None)
    assert not out
