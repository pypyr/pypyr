"""pypyrversion.py unit tests."""
import logging
import platform
from unittest.mock import patch
from pypyr.context import Context
import pypyr.steps.pypyrversion
import pypyr.version


def test_pypyr_version():
    logger = logging.getLogger('pypyr.steps.pypyrversion')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.pypyrversion.run_step({})

    mock_logger_info.assert_called_once_with(
        'pypyr version is: '
        f'pypyr {pypyr.version.__version__} '
        f'python {platform.python_version()}')


def test_pypyr_version_context_out_same_as_in():
    context = Context({'test': 'value1'})
    pypyr.steps.pypyrversion.run_step(context)
    assert context['test'] == 'value1', "context not returned from step."
