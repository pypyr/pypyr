"""string.py unit tests."""
import logging
import pypyr.parser.string
from tests.common.utils import patch_logger


def test_arg_string_parses_to_dict():
    """String input returns dictionary key argString."""
    out = pypyr.parser.string.get_parsed_context(['value 1,value 2, value3'])
    assert out['argString'] == 'value 1,value 2, value3'
    assert len(out) == 1, "1 item expected"


def test_arg_string_parses_to_single_entry():
    """Special chars input string should return string as is."""
    out = pypyr.parser.string.get_parsed_context([
        ', value1 # value 2 & value3'])
    assert out['argString'] == ', value1 # value 2 & value3'
    assert len(out) == 1, "1 item expected in context"


def test_arg_string_parses_list_to_single_entry():
    """Special chars input string should return string as is."""
    out = pypyr.parser.string.get_parsed_context([',',
                                                  ' value1 # ',
                                                  'value 2',
                                                  ' & value3'])
    assert out['argString'] == ',  value1 #  value 2  & value3'
    assert len(out) == 1, "1 item expected in context"


def test_empty_string_warns():
    """Empty input string should warn assert error."""
    with patch_logger(
            'pypyr.parser.string', logging.DEBUG) as mock_logger_debug:
        out = pypyr.parser.string.get_parsed_context(None)

    assert not out['argString']
    assert out['argString'] == ''
    mock_logger_debug.assert_called_with(
        "pipeline invoked without context arg set. For "
        "this string parser you're looking for something "
        "like: pypyr pipelinename spam and eggs")


def test_builtin_str_still_works():
    """Don't break built-in string keyword."""
    test_string = "arb string here"
    assert test_string.upper() == "ARB STRING HERE"
    assert test_string.count('arb') == 1
    assert isinstance(test_string, str)
