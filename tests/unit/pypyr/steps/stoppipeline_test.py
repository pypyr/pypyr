"""stoppipeline.py unit tests."""
import pytest
from pypyr.context import Context
from pypyr.errors import StopPipeline
import pypyr.steps.stoppipeline


def test_step_stoppipeline():
    """Stop raises stop."""
    with pytest.raises(StopPipeline):
        pypyr.steps.stoppipeline.run_step({})


def test_step_stoppipeline_context_same():
    """Stop doesn't nuke context."""
    context = Context({'test': 'value1'})
    with pytest.raises(StopPipeline):
        pypyr.steps.stoppipeline.run_step(context)
    assert context['test'] == 'value1', "context not returned from step."
