"""pypyr caching base class and functions."""
import logging
import threading

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class Cache():
    """Thread-safe general purpose cache for objects.

    Add things to the cache by calling get(key, creator). If the requested key
    doesn't exist, will add the item to the cache for you.
    """

    def __init__(self):
        """Instantiate the cache."""
        self._lock = threading.Lock()
        self._cache = {}

    def clear(self):
        """Clear the cache of all objects."""
        with self._lock:
            self._cache.clear()

    def get(self, key, creator):
        """Get key from cache. If key not exist, call creator and cache result.

        Looks for key in cache and returns object for that key.

        If key is not found, call creator and save the result to cache for that
        key.

        Be warned that get happens under the context of a Lock. . . so if
        creator takes a long time you might well be blocking.

        Args:
            key: key (unique id) of cached item
            creator: callable that will create cached object if key not found

        Returns:
            Cached item at key or the result of creator()
        """
        with self._lock:
            if key in self._cache:
                logger.debug("%s loading from cache", key)
                obj = self._cache[key]
            else:
                logger.debug("%s not found in cache. . . creating", key)
                obj = creator()
                self._cache[key] = obj

        return obj
