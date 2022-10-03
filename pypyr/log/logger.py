"""Logging functions for pypyr.

Configuration for the python logging library.
"""
import logging
import logging.config
import sys

from pypyr.config import config

NOTIFY = 25


class LevelFilter(logging.Filter):
    """Only let through messages < level."""

    def __init__(self, level: int) -> None:
        """Set the level at which and lower this filter will log."""
        self.level = level

    def filter(self, record):
        """Pass through records with level less than configured level."""
        return record.levelno < self.level


def set_logging_config(log_level, handlers):
    """Set python logging library config.

    Run this ONCE at the start of your process. It formats the python logging
    module's output.
    """
    if log_level is None:
        level = NOTIFY
        format_string = config.log_notify_format
    else:
        level = log_level
        format_string = config.log_detail_format

    logging.basicConfig(
        format=format_string,
        datefmt=config.log_date_format,
        level=level,
        handlers=handlers)


def notify(self, msg, *args, **kwargs):
    """Log a message with severity 'NOTIFY' on the root logger."""
    if self.isEnabledFor(NOTIFY):
        self._log(NOTIFY, msg, args, **kwargs)


def set_up_notify_log_level():
    """Add up a global notify severity to the python logging package.

    NOTIFY severity is logging level between INFO and WARNING. By default it
    outputs only echo step and step name with description.

    This function should run once and only once at the initialization of pypyr.
    You shouldn't need to do so yourself, it's called from package init.
    """
    # could (should?) be checking hasattr like so:
    # hasattr(logging, levelName):
    # hasattr(logging, methodName):
    # hasattr(logging.getLoggerClass(), methodName):
    # but this extra check is arguably *more* overhead than just assigning it?
    logging.addLevelName(NOTIFY, "NOTIFY")
    logging.NOTIFY = NOTIFY
    logging.getLoggerClass().notify = notify


def set_root_logger(log_level=None, log_path=None):
    """Set the root logger 'pypyr'. Do this before you do anything else.

    Run once and only once at initialization.

    log_level enumeration:
    10=DEBUG
    20=INFO
    25=NOTIFY (default)
    30=WARNING
    40=ERROR
    50=CRITICAL

    < 10 gives full traceback on errors.

    Args:
        log_level (int): Log level. If not specified, defaults to 25 - NOTIFY.
        log_path (path-like): File path+name. If specified, pypyr will append
            logging output to this indefinitely growing file and to the
            console.
    """
    if config.log_config:
        logging.config.dictConfig(config.log_config)
    else:
        handlers = get_log_handlers(log_level, log_path)
        set_logging_config(log_level, handlers=handlers)

    root_logger = logging.getLogger('pypyr')
    root_logger.debug(
        "Root logger %s configured with level %s",
        root_logger.name, log_level)


def get_log_handlers(log_level, log_path=None):
    """Return list of log handlers to handle stdout, stderr and file."""
    handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(LevelFilter(logging.WARNING))

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(max(logging.WARNING,
                                log_level or logging.NOTIFY))

    handlers.append(stdout_handler)
    handlers.append(stderr_handler)
    if log_path:
        file_handler = logging.FileHandler(log_path)
        handlers.append(file_handler)

    return handlers
