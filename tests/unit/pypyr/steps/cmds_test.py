"""pypyr.steps.cmd unit tests.

The bulk of the unit tests are in:
tests/unit/steps/dsl/cmdasync_test.py

For tests involving stdout & stderr set to files, see:
tests/integration/pypyr/steps/cmds_int_test.py
"""
from unittest.mock import patch

from pypyr.context import Context
import pypyr.steps.cmds


def test_cmds_step():
    """Use the AsyncCmdStep handler to run the step."""
    with patch('pypyr.steps.cmds.AsyncCmdStep') as mock_runner:
        pypyr.steps.cmds.run_step(Context({'a': 'b'}))

    mock_runner.assert_called_once_with(name='pypyr.steps.cmds',
                                        context={'a': 'b'},
                                        is_shell=False)
