"""python.py unit tests."""
import sys

from pypyr.context import Context
import pypyr.steps.python


def test_python_executable():
    """Python executable writes into context."""
    context = Context()
    pypyr.steps.python.run_step(context)
    assert context['python'] == sys.executable
    assert len(context) == 1
