"""jsonfile.py unit tests."""
import pypyr.parser.jsonfile
import pytest


def test_json_file_open_fails_on_arbitrary_string():
    """Non path-y input string should fail."""
    with pytest.raises(FileNotFoundError):
        pypyr.parser.jsonfile.get_parsed_context('value 1,value 2, value3')


def test_json_file_open_fails_on_empty_string():
    """Non path-y input string should fail."""
    with pytest.raises(AssertionError):
        pypyr.parser.jsonfile.get_parsed_context(None)


def test_json_pass():
    """Relative path to json should succeed."""
    context = pypyr.parser.jsonfile.get_parsed_context(
        ['./tests/testfiles/test.json'])

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context["key2"] == "value2", "key2 should be value2"
