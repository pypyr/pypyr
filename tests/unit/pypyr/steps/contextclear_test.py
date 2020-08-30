"""contextclear.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.contextclear
import pytest


def test_context_clear_throws_on_empty_context():
    """Context must exist."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.contextclear.run_step(Context())


def test_context_clear_throws_on_contextset_missing():
    """Context Clear must exist in context."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.contextclear.run_step(Context({'arbkey': 'arbvalue'}))


def test_context_clear_pass():
    """Context clear success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4',
        'contextClear': [
            'key2',
            'key4',
            'contextClear'
        ]
    })

    pypyr.steps.contextclear.run_step(context)

    assert len(context) == 2
    assert context['key1'] == 'value1'
    assert 'key2' not in context
    assert context['key3'] == 'value3'
    assert 'key4' not in context
    # recursion ahoy
    assert 'contextClear' not in context


def test_context_clear_no_raise_if_keys_dont_exist():
    """Context clear passes even if keys not in context."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4',
        'contextClear': [
            'key2',
            'key4',
            'key5',
            'key1',
        ]
    })

    pypyr.steps.contextclear.run_step(context)

    assert len(context) == 2
    assert 'key1' not in context
    assert 'key2' not in context
    assert context['key3'] == 'value3'
    assert 'key4' not in context
    # recursion ahoy
    assert context['contextClear'] == [
        'key2',
        'key4',
        'key5',
        'key1',
    ]
