"""stop.py unit tests."""
import pytest
from pypyr.context import Context
from pypyr.errors import Stop
import pypyr.steps.stop


def test_step_stop():
    with pytest.raises(Stop):
        pypyr.steps.stop.run_step({})


def test_step_stop_context_same():
    context = Context({'test': 'value1'})
    with pytest.raises(Stop):
        pypyr.steps.stop.run_step(context)
    assert context['test'] == 'value1', "context not returned from step."
