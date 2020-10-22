"""jsonfile.py unit tests."""
import pytest
import pypyr.parser.jsonfile


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


def test_json_parse_not_mapping_at_root():
    """Not mapping at root level raises."""
    with pytest.raises(TypeError) as err_info:
        pypyr.parser.jsonfile.get_parsed_context(
            ['./tests/testfiles/singleliteral.json'])

    assert str(err_info.value) == (
        "json input should describe an object at the top "
        "level. You should have something like\n"
        "{\n\"key1\":\"value1\",\n\"key2\":\"value2\"\n}\n"
        "at the json top-level, not an [array] or literal.")
