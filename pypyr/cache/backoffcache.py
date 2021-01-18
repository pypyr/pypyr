"""Global cache for retry back-off callables.

Attributes:
    backoff_cache: Global instance of the retry back-off callable cache.
                   Use this attribute to access the cache from elsewhere.
"""
import logging
from pypyr.cache.cache import Cache
import pypyr.moduleloader
import pypyr.retries

logger = logging.getLogger(__name__)


class BackoffCache(Cache):
    """Get retry strategy callable objects from the Backoff cache."""

    def __init__(self):
        """Initialize the cache with the built-in back-off strategies."""
        super().__init__()
        self._cache = pypyr.retries.builtin_backoffs.copy()

    def clear(self):
        """Clear the cache of all objects except built-in back-offs.."""
        with self._lock:
            # rather than iterating & selectively removing, just reset entirely
            self._cache = pypyr.retries.builtin_backoffs.copy()

    def get_backoff(self, name):
        """Get cached backoff callable. Adds to cache if not exist.

        Args:
            name: load the package.module.class specified & add the object
                reference to cache.

        Return:
            callable: the function/callable reference specified by name.
        """
        logger.debug("starting")

        backoff = self.get(name, lambda: load_backoff_callable(name))

        logger.debug("done")
        return backoff


# global instance of the cache. use this to access the cache from elsewhere.
backoff_cache = BackoffCache()


def load_backoff_callable(name):
    """Load the backoff retry callable specified by name.

    Args:
        name: (string) Absolute name of callable to load.

    Returns:
        Reference to the callable specified by name.
    """
    logger.debug("starting")

    module_name, dot, attr_name = name.rpartition('.')
    if not dot:
        # just a bare name, no dot, means must be in globals.
        # note that built-in backoffs already in cache, so this will only run
        # for bare names that aren't built-in back-offs.
        raise ValueError(
            f"Trying to find back-off strategy '{name}'. If this is a "
            "built-in back-off strategy, are you sure you got the name right?"
            "\nIf you're trying to load a custom callable, name should be in "
            "format 'package.module.ClassName' or 'mod.ClassName'.")

    backoff_module = pypyr.moduleloader.get_module(module_name)
    logger.debug("retry backoff strategy module loaded: %s", backoff_module)

    try:
        backoff_callable = getattr(backoff_module, attr_name)
    except AttributeError:
        logger.error(("Looking for retry back-off strategy %s. "
                      "The callable %s doesn't exist in module %s."),
                     name, attr_name, backoff_module)
        raise
    logger.debug("done")

    return backoff_callable
