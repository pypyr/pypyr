"""envget.py unit tests."""
import os
import pypyr.steps.envget
import pytest


def test_envget_throws_on_empty_context():
    """context must exist."""
    with pytest.raises(AssertionError):
        pypyr.steps.envget.run_step(None)


def test_envget_throws_on_envget_missing():
    """envSet must exist in context."""
    with pytest.raises(AssertionError):
        pypyr.steps.envget.run_step({'arbkey': 'arbvalue'})


def test_envget_pass():
    """envset success case"""
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb value from $ENV ARB_DELETE_ME2'

    context = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envGet': {
            'key2': 'ARB_DELETE_ME1',
            'key4': 'ARB_DELETE_ME2'
        }
    }

    pypyr.steps.envget.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'arb value from $ENV ARB_DELETE_ME1'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'arb value from $ENV ARB_DELETE_ME2'
