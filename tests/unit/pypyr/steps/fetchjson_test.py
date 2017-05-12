"""fetchjson.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fetchjson as filefetcher
import pytest


def test_fetchjson_no_path_raises():
    """None path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filefetcher.run_step(context)

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fetchJsonPath'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.fetchjson.\",)")


def test_fetchjson_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fetchJsonPath': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filefetcher.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fetchJsonPath'] must have a "
        "value for pypyr.steps.fetchjson.\",)")


def test_json_pass():
    """Relative path to json should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fetchJsonPath': './tests/testfiles/test.json'})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['ok1'] == 'ov1'
    assert context['fetchJsonPath'] == './tests/testfiles/test.json'
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"
