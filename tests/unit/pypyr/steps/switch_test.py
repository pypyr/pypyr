"""switch.py unit tests. Most of the tests are in pypyr.steps.dsl.cof."""
import pytest

from pypyr.context import Context
from pypyr.errors import Call
from pypyr.steps.switch import run_step


def test_switch_step_calls_cof():
    """Switch step calls through to dsl."""
    with pytest.raises(Call) as err:
        run_step(Context({
            'switch': [
                {'case': False, 'call': 'sg1'},
                {'case': True, 'call': 'sg2'}
            ]
        }))

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['sg2']
    assert cof.success_group is None
    assert cof.failure_group is None
    assert cof.original_config == ('switch', [
        {'case': False, 'call': 'sg1'},
        {'case': True, 'call': 'sg2'},
    ])


def test_switch_step_nothing():
    """No success match on switch case just carries on."""
    run_step(Context({
        'switch': [
            {'case': False, 'call': 'sg1'},
            {'case': False, 'call': 'sg2'}
        ]
    }))
