"""jsonparse.py unit tests."""
from pypyr.context import Context
from pypyr.dsl import SicString
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.jsonparse as jsonparse
import pytest


def test_jsonparse_no_jsonparse_raises():
    """No jsonparse input raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        jsonparse.run_step(context)

    assert str(err_info.value) == ("context['jsonParse'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.jsonparse.")


def test_jsonparse_no_json_raises():
    """No json raises."""
    context = Context({
        'jsonParse': {
            'a': 'b'}})

    with pytest.raises(KeyNotInContextError) as err_info:
        jsonparse.run_step(context)

    assert str(err_info.value) == (
        "context['jsonParse']['json'] doesn't exist. It must exist for "
        "pypyr.steps.jsonparse.")


def test_jsonparse_with_formatting():
    """Json with a root scalar works with out key."""
    context = Context({
        'k1': 'out',
        'k2': '{"a": "b", "c": "d"}',
        'jsonParse': {
            'json': '{k2:ff}',
            'key': '{k1}'}})

    jsonparse.run_step(context)

    assert context['out'] == {'a': 'b', 'c': 'd'}


def test_jsonparse_scalar_with_key():
    """Json with a root scalar works with out key."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': '1',
            'key': 'out'}})

    jsonparse.run_step(context)

    assert context['out'] == 1


def test_jsonparse_scalar_with_key_null():
    """Json with a root scalar works with out key and null value."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': 'null',
            'key': 'out'}})

    jsonparse.run_step(context)

    assert context['out'] is None


def test_jsonparse_scalar_with_key_empty():
    """Json with a root scalar works with out key and empty value."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': '',
            'key': 'out'}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        jsonparse.run_step(context)

    assert str(err_info.value) == (
        'jsonParse.json exists but is empty. It should be a valid json '
        'string for pypyr.steps.jsonparse. For example: '
        '\'{"key1": "value1", "key2": "value2"}\'')


def test_jsonparse_scalar_no_key_fails():
    """Json describing a scalar rather than a dict should fail if no outkey."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': '1'}})

    with pytest.raises(TypeError) as err_info:
        jsonparse.run_step(context)

    assert str(err_info.value) == (
        'json input should describe an object at the top level when '
        'jsonParse.key isn\'t specified. You should have something like '
        '\'{"key1": "value1", "key2": "value2"}\' in the json top-level, not '
        '["value1", "value2"]')


def test_jsonparse_map_no_key():
    """Json with a root mapping works with no key."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': SicString('{"a": "b", "c": "d"}')}})

    jsonparse.run_step(context)

    assert context == {
        'ok1': 'ov1',
        'jsonParse': {
            'json': SicString('{"a": "b", "c": "d"}')},
        'a': 'b',
        'c': 'd'}


def test_jsonparse_map_with_key():
    """Json with a root mapping works with out key."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': SicString('{"a": "b", "c": "d"}'),
            'key': 'out'}})

    jsonparse.run_step(context)

    assert context['out'] == {'a': 'b', 'c': 'd'}


def test_jsonparse_list_with_key():
    """Json with a root list works with out key."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': '[1, 2, 3]',
            'key': 'out'}})

    jsonparse.run_step(context)

    assert context['out'] == [1, 2, 3]


def test_jsonparse_list_fails():
    """Json describing a list rather than a dict should fail if no outkey."""
    context = Context({
        'ok1': 'ov1',
        'jsonParse': {
            'json': '[1, 2, 3]'}})

    with pytest.raises(TypeError) as err_info:
        jsonparse.run_step(context)

    assert str(err_info.value) == (
        'json input should describe an object at the top level when '
        'jsonParse.key isn\'t specified. You should have something like '
        '\'{"key1": "value1", "key2": "value2"}\' in the json top-level, not '
        '["value1", "value2"]')
