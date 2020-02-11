"""Continous Deployment logging functions.

Configuration for the python logging library.
"""
import logging


NOTIFY = 25


def set_logging_config(log_level, handlers):
    """Set python logging library config.

    Run this ONCE at the start of your process. It formats the python logging
    module's output.
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=log_level,
        handlers=handlers)


def notify(self, msg, *args, **kwargs):
    """Log a message with severity 'NOTIFY' on the root logger.
    """
    if self.isEnabledFor(NOTIFY):
        self._log(NOTIFY, msg, args, **kwargs)


def set_up_notify_log_level():
    """Add up a global notify severity to the python logging package.

    NOTIFY severity is logging level between INFO and WARNING.
    By default it outputs only echo step and step name
    with description.
    """

    # could (should?) be checking hasattr like so:
    # hasattr(logging, levelName):
    # hasattr(logging, methodName):
    # hasattr(logging.getLoggerClass(), methodName):
    # but this extra check is arguably *more* overhead than just assigning it?
    logging.addLevelName(NOTIFY, "NOTIFY")
    logging.NOTIFY = NOTIFY
    logging.getLoggerClass().notify = notify


def set_root_logger(log_level, log_path=None):
    """Set the root logger 'pypyr'. Do this before you do anything else.

    Run once and only once at initialization.
    """
    handlers = []

    console_handler = logging.StreamHandler()
    handlers.append(console_handler)
    if log_path:
        file_handler = logging.FileHandler(log_path)
        handlers.append(file_handler)

    set_logging_config(log_level, handlers=handlers)

    root_logger = logging.getLogger("pypyr")
    root_logger.debug(
        "Root logger %s configured with level %s",
        root_logger.name, log_level)
