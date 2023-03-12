"""Administrate pypyr caches."""
import logging

from pypyr.cache.backoffcache import backoff_cache
from pypyr.cache.filecache import file_cache
from pypyr.cache.loadercache import loader_cache
from pypyr.cache.namespacecache import pystring_namespace_cache
from pypyr.cache.parsercache import contextparser_cache
from pypyr.cache.stepcache import step_cache

logger = logging.getLogger(__name__)


def clear_all() -> None:
    """Clear all pypyr caches."""
    logger.debug("clearing all cache...")

    backoff_cache.clear()
    file_cache.clear()
    loader_cache.clear()
    pystring_namespace_cache.clear()
    contextparser_cache.clear()
    step_cache.clear()

    logger.debug("all cache cleared.")
