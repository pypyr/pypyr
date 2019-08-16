"""jump.py unit tests."""
import logging
import pytest
from pypyr.context import Context
from pypyr.errors import Jump
from pypyr.steps.jump import run_step

from tests.common.utils import patch_logger


def test_jump_step_dict_with_all_args():
    """Dict with all values set."""
    with pytest.raises(Jump) as err:
        with patch_logger('pypyr.steps.jump',
                          logging.INFO) as mock_logger_info:
            run_step(Context(Context({'jump': {'groups': ['b', 'c'],
                                               'success': 'sg',
                                               'failure': 'fg'}})))

    cof = err.value
    assert isinstance(cof, Jump)
    assert cof.groups == ['b', 'c']
    assert cof.success_group == 'sg'
    assert cof.failure_group == 'fg'

    mock_logger_info.assert_called_once_with(
        "step pypyr.steps.jump about to hand over control with jump: "
        "Will run groups: ['b', 'c']  with success sg and failure fg")
