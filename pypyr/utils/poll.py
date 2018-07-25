"""Utility functions for polling."""
import time
import logging

# pypyr logger means the log level will be set correctly and output formatted.
logger = logging.getLogger(__name__)


def wait_until_true(interval, max_attempts):
    """Decorator that executes a function until it returns True.

    Executes wrapped function at every number of seconds specified by interval,
    until wrapped function either returns True or max_attempts are exhausted,
    whichever comes 1st. The wrapped function can have any given signature.

    Use me if you always want to time out at max_attempts and you don't care
    about the while loop position counter value. If you do care, use
    while_until_true instead.

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
            logger.debug("done")
            return False
        return sleep_looper

    return decorator


def while_until_true(interval, max_attempts):
    """Decorator that executes a function until it returns True.

    Executes wrapped function at every number of seconds specified by interval,
    until wrapped function either returns True or max_attempts are exhausted,
    whichever comes 1st.

    The difference between while_until_true and wait_until_true is that the
    latter will always loop to a max_attempts, whereas while_until_true will
    keep going indefinitely.

    The other notable difference to wait_until_true is that the wrapped
    function signature must be:
    func(counter, *args, **kwargs)

    This is because this decorator injects the while loop counter into the
    invoked function.

    Args:
        interval: In seconds. How long to wait between executing the wrapped
                  function.
        max_attempts: int. Execute wrapped function up to this limit. None
                      means infinite (or until wrapped function returns True).
                      Passing anything <0 also means infinite.

    Returns:
        Bool. True if wrapped function returned True. False if reached
              max_attempts without the wrapped function ever returning True.
    """
    def decorator(f):
        logger.debug("started")

        def sleep_looper(*args, **kwargs):
            if max_attempts:
                logger.debug(f"Looping every {interval} seconds for "
                             f"{max_attempts} attempts")
            else:
                logger.debug(f"Looping every {interval} seconds.")

            i = 0
            result = False

            # pragma for coverage: cov can't figure out the branch construct
            # with the dynamic function invocation, it seems, so marks the
            # branch partial. unit test cov is 100%, though.
            while not result:  # pragma: no branch
                i += 1
                result = f(i, *args, **kwargs)
                if result:
                    logger.debug(f"iteration {i}. Desired state reached.")
                    break
                elif max_attempts:
                    if i < max_attempts:
                        logger.debug(f"iteration {i}. Still waiting. . .")
                        time.sleep(interval)
                    else:
                        logger.debug(f"iteration {i}. Max attempts exhausted.")
                        break
                else:
                    # result False AND max_attempts is None means keep looping
                    # because None = infinite
                    logger.debug(f"iteration {i}. Still waiting. . .")
                    time.sleep(interval)
            logger.debug("done")
            return result

        return sleep_looper

    return decorator
