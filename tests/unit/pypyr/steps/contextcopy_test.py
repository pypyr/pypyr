"""contextcopy.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.contextcopy
import pytest


def test_context_copy_throws_on_empty_context():
    """Input context must exist."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.contextcopy.run_step(Context())


def test_context_copy_throws_on_contextcopy_missing():
    """Input contextcopy must exist in context."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.contextcopy.run_step(Context({'arbkey': 'arbvalue'}))

    assert str(err_info.value) == ("context['contextCopy'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.contextcopy.")


def test_context_copy_pass():
    """Input contextcopy success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'contextCopy': {
            'key2': 'key1',
            'key4': 'key3'
        }
    })

    pypyr.steps.contextcopy.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value1'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value3'
