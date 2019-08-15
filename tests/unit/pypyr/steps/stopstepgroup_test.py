"""stopstepgroup.py unit tests."""
import pytest
from pypyr.context import Context
from pypyr.errors import StopStepGroup
import pypyr.steps.stopstepgroup


def test_step_stopstepgroup():
    with pytest.raises(StopStepGroup):
        pypyr.steps.stopstepgroup.run_step({})


def test_step_stopstepgroup_context_same():
    context = Context({'test': 'value1'})
    with pytest.raises(StopStepGroup):
        pypyr.steps.stopstepgroup.run_step(context)
    assert context['test'] == 'value1', "context not returned from step."
