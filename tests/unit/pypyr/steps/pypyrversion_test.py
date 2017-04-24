"""pypyrversion.py unit tests."""
from pypyr.context import Context
import pypyr.log.logger
import pypyr.steps.pypyrversion


def test_pypyr_version():
    pypyr.steps.pypyrversion.run_step({})


def test_pypyr_version_context_out_same_as_in():
    context = Context({'test': 'value1'})
    pypyr.steps.pypyrversion.run_step(context)
    assert context['test'] == 'value1', "context not returned from step."
