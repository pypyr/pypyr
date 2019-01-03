"""string.py unit tests."""
import logging
from unittest.mock import patch
import pypyr.parser.string


def test_comma_string_parses_to_dict():
    """String input returns dictionary key argString."""
    out = pypyr.parser.string.get_parsed_context('value 1,value 2, value3')
    assert out['argString'] == 'value 1,value 2, value3'
    assert len(out) == 1, "1 item expected"


def test_no_commas_string_parses_to_single_entry():
    """Special chars input string should return string as is."""
    out = pypyr.parser.string.get_parsed_context(', value1 # value 2 & value3')
    assert out['argString'] == ', value1 # value 2 & value3'
    assert len(out) == 1, "1 item expected in context"


def test_empty_string_throw():
    """Empty input string should throw assert error."""
    logger = logging.getLogger('pypyr.parser.string')

    with patch.object(logger, 'debug') as mock_logger_debug:
        out = pypyr.parser.string.get_parsed_context(None)

    assert out['argString'] is None
    mock_logger_debug.assert_called_once_with(
        "pipeline invoked without context arg set. For "
        "this string parser you're looking for something "
        "like: pypyr pipelinename 'spam and eggs'.")


def test_builtin_list_still_works():
    """Don't break built-in string keyword."""
    test_string = "arb string here"
    assert test_string.upper() == "ARB STRING HERE"
    assert test_string.count('arb') == 1
    assert isinstance(test_string, str)
