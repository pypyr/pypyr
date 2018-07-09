"""echo.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.log.logger
import pypyr.steps.echo
import pytest
from unittest.mock import patch


def test_echo_pass():
    """Echos echoMe in context."""
    context = Context({
        'echoMe': 'test value here'})

    logger = pypyr.log.logger.get_logger('pypyr.steps.echo')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.echo.run_step(context)

    mock_logger_info.assert_called_once_with('test value here')


def test_echo_substitutions_pass():
    """Format string interpolations should work."""
    context = Context({
        'key1': 'down the',
        'echoMe': 'piping {key1} valleys wild'})

    logger = pypyr.log.logger.get_logger('pypyr.steps.echo')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.echo.run_step(context)

    mock_logger_info.assert_called_once_with('piping down the valleys wild')


def test_echo_number_pass():
    """An int should echo."""
    context = Context({
        'echoMe': 77})

    logger = pypyr.log.logger.get_logger('pypyr.steps.echo')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.echo.run_step(context)

    mock_logger_info.assert_called_once_with(77)


def test_echo_bool_pass():
    """A bool should echo."""
    context = Context({
        'echoMe': False})

    logger = pypyr.log.logger.get_logger('pypyr.steps.echo')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.echo.run_step(context)

    mock_logger_info.assert_called_once_with(False)


def test_echo_empty_context_fails():
    """Empty context fails."""
    with pytest.raises(AssertionError) as err_info:
        pypyr.steps.echo.run_step(None)

    assert repr(err_info.value) == ("AssertionError(\"context must be set for "
                                    "echo. Did you set 'echoMe=text "
                                    "here'?\",)")


def test_echo_missing_echo_me_raises():
    """context must contain echoMe."""
    context = Context({
        'blah': 'blah blah'})
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.echo.run_step(context)

    assert repr(err_info.value) == ("KeyNotInContextError(\"context['echoMe'] "
                                    "doesn't exist. It must exist for "
                                    "pypyr.steps.echo.\",)")


def test_echo_echo_me_none_pass():
    """Echo can output None."""
    context = Context({'echoMe': None})
    logger = pypyr.log.logger.get_logger('pypyr.steps.echo')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.echo.run_step(context)

    mock_logger_info.assert_called_once_with(None)
