"""pypyrversion.py unit tests."""
import logging
import platform
from pypyr.context import Context
import pypyr.steps.pypyrversion
import pypyr.version
from tests.common.utils import patch_logger


def test_pypyr_version():
    """Return version as expected."""
    with patch_logger(
            'pypyr.steps.pypyrversion', logging.NOTIFY
    ) as mock_logger_notify:
        pypyr.steps.pypyrversion.run_step({})

    mock_logger_notify.assert_called_once_with(
        f'pypyr {pypyr.version.__version__} '
        f'python {platform.python_version()}')


def test_pypyr_version_context_out_same_as_in():
    """Context does not mutate."""
    context = Context({'test': 'value1'})
    pypyr.steps.pypyrversion.run_step(context)
    assert context['test'] == 'value1', "context not returned from step."
