"""Global cache for pipelines found by pypyr.loaders.file.

Map file path to file contents.

Attributes:
    file_cache: Global instance of the file loader cache.
                Use this attribute to access the cache from elsewhere.
"""

from pypyr.cache.cache import Cache

file_cache = Cache()
