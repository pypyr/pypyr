"""logger.py unit tests."""
import logging
from unittest.mock import patch
import pypyr.log.logger
from tests.common.utils import patch_logger


def test_logger_with_console_handler():
    """Root logger instantiates with just the console handler."""
    log_path = None
    with patch.object(logging, 'basicConfig') as mock_logger:
        pypyr.log.logger.set_root_logger(10, log_path)

    mock_logger.assert_called_once()
    args, kwargs = mock_logger.call_args
    assert kwargs['format'] == (
        '%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s')
    assert kwargs['datefmt'] == '%Y-%m-%d %H:%M:%S'
    assert kwargs['level'] == 10
    assert len(kwargs['handlers']) == 1
    assert isinstance(kwargs['handlers'][0], logging.StreamHandler)


def test_logger_with_file_and_console_handler():
    """Root logger instantiates with console and file handler both."""
    log_path = '/arb/path/here'
    with patch.object(logging, 'basicConfig') as mock_logger:
        with patch('logging.FileHandler',
                   spec=logging.FileHandler) as mock_filehandler:
            pypyr.log.logger.set_root_logger(10, log_path)

    mock_logger.assert_called_once()
    mock_filehandler.assert_called_once_with(log_path)
    args, kwargs = mock_logger.call_args
    assert kwargs['format'] == (
        '%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s')
    assert kwargs['datefmt'] == '%Y-%m-%d %H:%M:%S'
    assert kwargs['level'] == 10
    assert len(kwargs['handlers']) == 2
    assert isinstance(kwargs['handlers'][0], logging.StreamHandler)
    assert isinstance(kwargs['handlers'][1], logging.FileHandler)


def test_notice_log_level_available():
    """Notify log level added."""
    # actually redundant, coz ./conftest.py actually already calls
    # set_up_notify_log_level. Might as well test re-entrancy then, thus:
    pypyr.log.logger.set_up_notify_log_level()

    assert logging.INFO < logging.NOTIFY < logging.WARNING

    logger = logging.getLogger('pypyr')
    with patch_logger('pypyr', logging.NOTIFY) as mock_logger_notify:
        logger.notify("Arb message: %s", "arb value")

        logger.setLevel(logging.WARNING)
        logger.notify("Not logged record")

    mock_logger_notify.assert_called_once_with("Arb message: arb value")
