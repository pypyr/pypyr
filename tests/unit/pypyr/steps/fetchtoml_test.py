"""fetchtoml.py unit tests."""
from unittest.mock import mock_open, patch

import pytest

try:
    # can get rid of the try soon as py 3.11 min supported version
    # reason is py 3.11 includes tomli in stdlib
    from tomllib import TOMLDecodeError
except ModuleNotFoundError:
    from tomli import TOMLDecodeError

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fetchtoml as tomlfetcher


def test_fetch_toml_no_path_raises():
    """None path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        tomlfetcher.run_step(context)

    assert str(err_info.value) == ("context['fetchToml'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fetchtoml.")


def test_fetch_toml_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fetchToml': {
            'path': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        tomlfetcher.run_step(context)

    assert str(err_info.value) == ("context['fetchToml']['path'] must have a "
                                   "value for pypyr.steps.fetchtoml.")


def test_fetch_toml_pass(fs):
    """Relative path to toml should succeed."""
    in_path = './tests/testfiles/test.toml'
    fs.create_file(in_path, contents="""key1 = "value1"
key2 = "value2"
key3 = "value3"
""")

    context = Context({
        'ok1': 'ov1',
        'fetchToml': {
            'path': in_path}})

    tomlfetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchTomlPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


def test_fetch_toml_pass_with_string(fs):
    """Relative path to toml should succeed with string input."""
    in_path = './tests/testfiles/test.toml'
    fs.create_file(in_path, contents="""key1 = "value1"
key2 = "value2"
key3 = "value3"
""")

    context = Context({
        'ok1': 'ov1',
        'fetchToml': in_path})

    tomlfetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchTomlPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


def test_fetch_toml_pass_with_path_substitution(fs):
    """Relative path to toml with string substitution on path."""
    in_path = './tests/testfiles/test.toml'
    fs.create_file(in_path, contents="""key1 = "value1"
key2 = "value2"
key3 = "value3"
""")

    context = Context({
        'ok1': 'ov1',
        'fileName': 'test',
        'fetchToml': {
            'path': './tests/testfiles/{fileName}.toml'}})

    tomlfetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['ok1'] == 'ov1'
    assert 'fetchTomlPath' not in context
    assert context["key1"] == "value1", "key1 should be value2"
    assert context["key2"] == "value2", "key2 should be value2"
    assert context["key3"] == "value3", "key3 should be value2"


def test_fetchtoml_with_destination():
    """Toml writes to destination key."""
    context = Context({
        'fetchToml': {
            'path': '/arb/arbfile',
            'key': 'outkey'}})

    toml_bytes = b'k1 = "v1"\nk2 = "v2"'
    with patch('pypyr.toml.open', mock_open(read_data=toml_bytes)):
        tomlfetcher.run_step(context)

    assert context['outkey'] == {'k1': 'v1', 'k2': 'v2'}
    assert len(context) == 2


def test_fetchtoml_with_destination_int():
    """Toml writes to destination key that's not a string."""
    context = Context({
        'fetchToml': {
            'path': '/arb/arbfile',
            'key': 99}})

    toml_bytes = b'k1 = "v1"\nk2 = "v2"'
    with patch('pypyr.toml.open', mock_open(read_data=toml_bytes)):
        tomlfetcher.run_step(context)

    assert context[99] == {'k1': 'v1', 'k2': 'v2'}
    assert len(context) == 2


def test_fetchtoml_with_destination_formatting():
    """Toml writes to destination key found by formatting expression."""
    context = Context({
        'keyhere': {'sub': ['outkey', 2, 3]},
        'fetchToml': {
            'path': '/arb/arbfile',
            'key': '{keyhere[sub][0]}'}})

    toml_bytes = b'1 = 2\n2 = 3'
    with patch('pypyr.toml.open', mock_open(read_data=toml_bytes)):
        tomlfetcher.run_step(context)

    assert len(context) == 3
    # toml spec always interprets keys as strings
    assert context['outkey'] == {'1': 2, '2': 3}
    assert context['keyhere'] == {'sub': ['outkey', 2, 3]}


def test_fetchtoml_invalid_toml_fails():
    """Invalid toml document fails to load."""
    context = Context({
        'ok1': 'ov1',
        'fetchToml': {
            'path': '/arb/arbfile'}})

    with patch('pypyr.toml.open', mock_open(read_data=b'[1,2,3]')):
        with pytest.raises(TOMLDecodeError):
            tomlfetcher.run_step(context)
