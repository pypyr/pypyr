"""envunset.py unit tests."""
import os
from pypyr.context import Context
import pypyr.steps.envunset
import pytest


def test_envunset_throws_on_empty_context():
    """context must exist."""
    with pytest.raises(AssertionError):
        pypyr.steps.envunset.run_step(Context())


def test_envset_throws_on_envset_missing():
    """envUnset must exist in context."""
    with pytest.raises(AssertionError) as err_info:
        pypyr.steps.envunset.run_step(Context({'arbkey': 'arbvalue'}))

    assert repr(err_info.value) == ("AssertionError(\"context['envUnset'] "
                                    "doesn't exist. It must have a value for "
                                    "pypyr.steps.envunset.\",)")


def test_envset_pass():
    """envUnset success case"""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    os.environ['ARB_DELETE_ME1'] = 'arb from pypyr context ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envUnset': [
            'ARB_DELETE_ME1',
            'ARB_DELETE_ME2'
        ]
    })

    pypyr.steps.envunset.run_step(context)

    assert 'ARB_DELETE_ME1' not in os.environ
    assert 'ARB_DELETE_ME2' not in os.environ


def test_envset_doesnt_exist():
    """envUnset success case"""
    # Make sure $ENV isn't set
    try:
        del os.environ['ARB_DELETE_SNARK']
    except KeyError:
        pass

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envUnset': [
            'ARB_DELETE_SNARK'
        ]
    })

    pypyr.steps.envunset.run_step(context)

    assert 'ARB_DELETE_SNARK' not in os.environ
