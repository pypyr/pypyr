"""Utility functions for polling."""
import time
import logging

# pypyr logger means the log level will be set correctly and output formatted.
logger = logging.getLogger(__name__)


def wait_until_true(interval, max_attempts):
    """Decorator that executes a function until it returns True.

    Executes wrapped function at every number of seconds specified by interval,
    until wrapped function either returns True or max_attempts are exhausted,
    whichever comes 1st.

    Args:
        interval: In seconds. How long to wait between executing the wrapped
                  function.
        max_attempts: int. Execute wrapped function up to this limit.

    Returns:
        Bool. True if wrapped function returned True. False if reached
              max_attempts without the wrapped function ever returning True.
    """
    def decorator(f):
        logger.debug("started")

        def sleep_looper(*args, **kwargs):
            logger.debug(f"Looping every {interval} seconds for "
                         f"{max_attempts} attempts")
            for i in range(1, max_attempts + 1):
                result = f(*args, **kwargs)
                if result:
                    logger.debug(f"iteration {i}. Desired state reached.")
                    return True
                if i < max_attempts:
                    logger.debug(f"iteration {i}. Still waiting. . .")
                    time.sleep(interval)
            return False
        return sleep_looper

    logger.debug("done")
    return decorator
