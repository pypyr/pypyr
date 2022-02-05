"""fetchjson.py unit tests."""
from unittest.mock import mock_open, patch

import pytest

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fetchjson as filefetcher


def test_fetchjson_no_path_raises():
    """None path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filefetcher.run_step(context)

    assert str(err_info.value) == ("context['fetchJson'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fetchjson.")


def test_fetchjson_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fetchJson': {
            'path': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filefetcher.run_step(context)

    assert str(err_info.value) == ("context['fetchJson']['path'] must have a "
                                   "value for pypyr.steps.fetchjson.")


def test_json_pass(fs):
    """Relative path to json should succeed."""
    payload = """{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
"""
    in_path = './tests/testfiles/test.json'

    fs.create_file(in_path, contents=payload)
    context = Context({
        'ok1': 'ov1',
        'fetchJson': {
            'path': in_path}})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchJsonPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


def test_json_pass_with_string(fs):
    """Relative path to json should succeed with string input."""
    payload = """{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
"""
    in_path = './tests/testfiles/test.json'

    fs.create_file(in_path, contents=payload)

    context = Context({
        'ok1': 'ov1',
        'fetchJson': './tests/testfiles/test.json'})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchJsonPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


def test_json_pass_with_path_substitution(fs):
    """Relative path to json succeeds with string substitution on path."""
    payload = """{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
"""
    in_path = './tests/testfiles/test.json'

    fs.create_file(in_path, contents=payload)

    context = Context({
        'ok1': 'ov1',
        'fileName': 'test',
        'fetchJson': {
            'path': './tests/testfiles/{fileName}.json'}})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchJsonPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


@patch('pypyr.config.config.default_encoding', new='utf-16')
def test_json_pass_with_encoding_from_config(fs):
    """Json loads with encoding from config."""
    payload = """{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
"""
    in_path = './tests/testfiles/test.json'

    fs.create_file(in_path, contents=payload, encoding='utf-16')

    context = Context({
        'ok1': 'ov1',
        'fileName': 'test',
        'fetchJson': {
            'path': './tests/testfiles/{fileName}.json'}})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchJsonPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


@patch('pypyr.config.config.default_encoding', new='ascii')
def test_json_pass_with_encoding_from_input(fs):
    """Json loads with encoding from input."""
    payload = """{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
"""
    in_path = './tests/testfiles/test.json'

    fs.create_file(in_path, contents=payload, encoding='utf-16')

    context = Context({
        'ok1': 'ov1',
        'fileName': 'test',
        'enc': 'utf-16',
        'fetchJson': {
            'path': './tests/testfiles/{fileName}.json',
            'encoding': '{enc}'}})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchJsonPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


def test_fetchjson_with_destination():
    """Json writes to destination key."""
    context = Context({
        'fetchJson': {
            'path': '/arb/arbfile',
            'key': 'outkey'}})

    with patch('pypyr.steps.fetchjson.open', mock_open(read_data='[1,2,3]')):
        filefetcher.run_step(context)

    assert context['outkey'] == [1, 2, 3]
    assert len(context) == 2


def test_fetchjson_with_destination_int():
    """Json writes to destination key that's not a string."""
    context = Context({
        'fetchJson': {
            'path': '/arb/arbfile',
            'key': 99}})

    with patch('pypyr.steps.fetchjson.open', mock_open(read_data='[1,2,3]')):
        filefetcher.run_step(context)

    assert context[99] == [1, 2, 3]
    assert len(context) == 2


def test_fetchjson_with_destination_formatting():
    """Json writes to destination key found by formatting expression."""
    context = Context({
        'keyhere': {'sub': ['outkey', 2, 3]},
        'fetchJson': {
            'path': '/arb/arbfile',
            'key': '{keyhere[sub][0]}'}})

    with patch('pypyr.steps.fetchjson.open', mock_open(
            read_data='{"1": 2,"2": 3}')):
        filefetcher.run_step(context)

    assert len(context) == 3
    assert context['outkey'] == {'1': 2, '2': 3}
    assert context['keyhere'] == {'sub': ['outkey', 2, 3]}


def test_fetchjson_list_fails():
    """Json describing a list rather than a dict should fail if no outkey."""
    context = Context({
        'ok1': 'ov1',
        'fetchJson': {
            'path': '/arb/arbfile'}})

    with patch('pypyr.steps.fetchjson.open', mock_open(read_data='[1,2,3]')):
        with pytest.raises(TypeError):
            filefetcher.run_step(context)
