"""Global cache for namespace imports.

Attributes:
    pystring_namespace_cache: global instance of the namespace cache for
        PyString expressions. Use this attribute to access the cache from
        elsewhere.
"""
import logging
from sys import intern
from pypyr.cache.cache import Cache
from pypyr.moduleloader import ImportVisitor


logger = logging.getLogger(__name__)


class NamespaceCache(Cache):
    """Cache of namespace dictionaries.

    Parse source string for python import statements using AST Visitor.
    """

    def get_namespace(self, source):
        """Get cached namespace. Adds to cache if not exist.

        Args:
            source (str): String with python 'import x.y'/'from x import y'
                statements.

        Returns:
            Namespace dictionary of imported references.
        """
        logger.debug("starting")

        # source can be relatively long.
        # interning means cache dict compare obj id rather than full str parse
        interned_source = intern(source)
        namespace = self.get(
            interned_source,
            lambda: ImportVisitor().get_namespace(interned_source))

        logger.debug("done")
        return namespace


# global instance of the cache. use this to access the cache from elsewhere.
pystring_namespace_cache = NamespaceCache()
