"""echo.py unit tests."""
import logging
import pytest
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.echo

from tests.common.utils import patch_logger


def test_echo_pass():
    """Echo echoMe in context."""
    context = Context({
        'echoMe': 'test value here'})

    with patch_logger(
            'pypyr.steps.echo', logging.NOTIFY) as mock_logger_notify:
        pypyr.steps.echo.run_step(context)

    mock_logger_notify.assert_called_once_with('test value here')


def test_echo_substitutions_pass():
    """Format string interpolations should work."""
    context = Context({
        'key1': 'down the',
        'echoMe': 'piping {key1} valleys wild'})

    with patch_logger(
            'pypyr.steps.echo', logging.NOTIFY) as mock_logger_notify:
        pypyr.steps.echo.run_step(context)

    mock_logger_notify.assert_called_once_with('piping down the valleys wild')


def test_echo_number_pass():
    """An int should echo."""
    context = Context({
        'echoMe': 77})

    with patch_logger(
            'pypyr.steps.echo', logging.NOTIFY) as mock_logger_notify:
        pypyr.steps.echo.run_step(context)

    mock_logger_notify.assert_called_once_with(str(77))


def test_echo_bool_pass():
    """A bool should echo."""
    context = Context({
        'echoMe': False})

    with patch_logger(
            'pypyr.steps.echo', logging.NOTIFY) as mock_logger_notify:
        pypyr.steps.echo.run_step(context)

    mock_logger_notify.assert_called_once_with(str(False))


def test_echo_empty_context_fails():
    """Empty context fails."""
    with pytest.raises(AssertionError) as err_info:
        pypyr.steps.echo.run_step(None)

    assert str(err_info.value) == ("context must be set for "
                                   "echo. Did you set 'echoMe=text "
                                   "here'?")


def test_echo_missing_echo_me_raises():
    """Context must contain echoMe."""
    context = Context({
        'blah': 'blah blah'})
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.echo.run_step(context)

    assert str(err_info.value) == ("context['echoMe'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.echo.")


def test_echo_echo_me_none_pass():
    """Echo can output None."""
    context = Context({'echoMe': None})
    with patch_logger(
            'pypyr.steps.echo', logging.NOTIFY) as mock_logger_notify:
        pypyr.steps.echo.run_step(context)

    mock_logger_notify.assert_called_once_with(str(None))
