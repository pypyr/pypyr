"""contextset.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.contextset
import pytest


def test_context_set_throws_on_empty_context():
    """context must exist."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.contextset.run_step(Context())


def test_context_set_throws_on_contextset_missing():
    """contextSet must exist in context."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.contextset.run_step(Context({'arbkey': 'arbvalue'}))

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['contextSet'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.contextset.\",)")


def test_context_set_pass():
    """contextset success case"""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'contextSet': {
            'key2': 'key1',
            'key4': 'key3'
        }
    })

    pypyr.steps.contextset.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value1'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value3'
