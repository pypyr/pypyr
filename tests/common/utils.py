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
    """Adds a new mocked handler to the logger, which will store
    formatted log records with the only one specified level.

    If logging level is DEBUG, will take care only about DEBUG
    records and will not report other levels even higher(INFO, ERROR and etc).
    """
    logger = logging.getLogger(name)
    logging_level = logger.level
    if level < logging_level or not logging_level:
        logger.setLevel(level)

    stream = Mock()
    stream.write = Mock()

    handler = logging.StreamHandler(stream)
    handler.terminator = ''
    handler.setLevel(level)

    def mock_handle(record):
        if record.levelno == level:
            logging.StreamHandler.handle(handler, record)

    handler.handle = mock_handle
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

    try:
        yield stream.write
    finally:
        logger.removeHandler(handler)
        logger.setLevel(logging_level)
