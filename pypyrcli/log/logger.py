"""Continous Deployment logging functions.

Configuration for the python logging library.
"""
import logging

log_level = 0


def get_logger(logger_name):
    """Create a logger with the log_level set."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    return logger


def set_logging_config():
    """Set python logging library config.

    Run this ONCE at the start of your process. It formats the python logging
    module's output.
    Defaults logging level to INFO = 20)
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)
