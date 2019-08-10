"""Global cache for context_parser modules.

Attributes:
    contextparser_cache: global instance of the context_parser cache.
                      Use this attribute to access the cache from elsewhere.
"""
import logging
from pypyr.cache.cache import Cache
import pypyr.moduleloader

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class ContextParserCache(Cache):
    """Get functions from the pypeloader cache."""

    def get_context_parser(self, parser_module_name):
        """Get cached get_parsed_context function. Adds to cache if not exist.

        Args:
            parser_module_name: load the module specified by this, get its
                                get_parsed_context function and add it to
                                cache.

        Return:
            function: the get_parsed_context function of module specified
                      by parser_module_name.
        """
        logger.debug("starting")

        parser_function = self.get(parser_module_name,
                                   lambda: load_the_parser(parser_module_name))

        logger.debug("done")
        return parser_function


# global instance of the cache. use this to access the cache from elsewhere.
contextparser_cache = ContextParserCache()


def load_the_parser(parser_module_name):
    """Loads the module specified by parser_module_name, returns its function.

    Args:
        parser_module_name: string: name of module to load

    Returns:
        function: the get_parsed_context function in the module
    """
    logger.debug("starting")

    parser_module = pypyr.moduleloader.get_module(parser_module_name)
    logger.debug("context parser module found: %s", parser_module_name)

    try:
        get_parsed_context = getattr(
            parser_module, 'get_parsed_context'
        )
    except AttributeError:
        logger.error(
            "The context parser %s doesn't have a "
            "get_parsed_context(context_arg): "
            "function.",
            parser_module_name
        )
        raise

    logger.debug("done")
    return get_parsed_context
