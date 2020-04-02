"""call.py unit tests."""
import logging
import pytest
from pypyr.context import Context
from pypyr.errors import Call
from pypyr.steps.call import run_step

from tests.common.utils import patch_logger


def test_call_step_dict_with_all_args():
    """Dict with all values set."""
    with pytest.raises(Call) as err:
        with patch_logger('pypyr.steps.call',
                          logging.INFO) as mock_logger_info:
            run_step(Context(Context({'call': {'groups': ['b', 'c'],
                                               'success': 'sg',
                                               'failure': 'fg'}})))

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b', 'c']
    assert cof.success_group == 'sg'
    assert cof.failure_group == 'fg'
    assert cof.original_config == ('call', {'groups': ['b', 'c'],
                                            'success': 'sg',
                                            'failure': 'fg'})

    mock_logger_info.assert_called_once_with(
        "step pypyr.steps.call about to hand over control with call: "
        "Will run groups: ['b', 'c']  with success sg and failure fg")
