"""Utility methods for test."""
import logging
from contextlib import contextmanager
from copy import deepcopy
from unittest.mock import MagicMock, Mock


class DeepCopyMagicMock(MagicMock):
    """Derive a new MagicMock doing a deepcopy of args to calls.

    MagicMocks store a reference to a mutable object - so on multiple calls to
    the mock the call history isn't maintained if the same obj mutates as an
    arg to those calls. https://bugs.python.org/issue33667

    It's probably not sensible to deepcopy all mock calls. So this little class
    is for patching the MagicMock class specifically, where it will do the
    deepcopy only where specifically patched.

    See here:
    https://docs.python.org/3/library/unittest.mock-examples.html#coping-with-mutable-arguments
    """

    def __call__(self, *args, **kwargs):
        """Mock call override does deepcopy."""
        return super(DeepCopyMagicMock, self).__call__(*deepcopy(args),
                                                       **deepcopy(kwargs))


@contextmanager
def patch_logger(name, level=logging.DEBUG):
    """Add a new mocked handler to the logger.

    Will store formatted log records with the only one specified level.

    If logging level is DEBUG, will take care only about DEBUG
    records and will not report other levels even higher(INFO, ERROR and etc).
    """
    logger = logging.getLogger(name)
    logging_level = logger.level
    if level < logging_level or not logging_level:
        logger.setLevel(level)

    mock = Mock()

    class MockHandler(logging.NullHandler):
        def handle(self, record):
            if record.levelno == level:
                mock(self.format(record))

    handler = MockHandler(level)
    logger.addHandler(handler)

    try:
        yield mock
    finally:
        # restore logger settings
        logger.removeHandler(handler)
        logger.setLevel(logging_level)


def read_file_to_list(path):
    """Read path and write each line to list.

    Args:
        path: path-like. Path to file to read.

    Returns:
        list of str. Each line in file is an item on the list.
    """
    with open(path, 'r') as file:
        return [line.rstrip() for line in file.readlines()]
