"""envset.py unit tests."""
import os
import pypyr.steps.envset
import pytest


def test_envset_throws_on_empty_context():
    """context must exist."""
    with pytest.raises(AssertionError):
        pypyr.steps.envset.run_step(None)


def test_envset_throws_on_envset_missing():
    """envGet must exist in context."""
    with pytest.raises(AssertionError):
        pypyr.steps.envset.run_step({'arbkey': 'arbvalue'})


def test_envset_pass():
    """envset success case"""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    del os.environ['ARB_DELETE_ME1']
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envSet': {
            'ARB_DELETE_ME1': 'key2',
            'ARB_DELETE_ME2': 'key1'
        }
    }

    pypyr.steps.envset.run_step(context)

    assert os.environ['ARB_DELETE_ME1'] == 'value2'
    assert os.environ['ARB_DELETE_ME2'] == 'value1'

    del os.environ['ARB_DELETE_ME1']
    del os.environ['ARB_DELETE_ME2']
