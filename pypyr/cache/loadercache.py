"""Global cache for pypeloader modules.

Attributes:
    pypeloader_cache: global instance of the loader cache.
                      Use this attribute to access the cache from elsewhere.
"""
import logging
from pypyr.cache.cache import Cache
import pypyr.moduleloader

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class PypeLoaderCache(Cache):
    """Get functions from the pypeloader cache."""

    def get_pype_loader(self, loader=None):
        """Get cached get_pipeline_definition function.

        Defaults to pypyr.pypeloaders.fileloader if loader not specified.

        Args:
            loader: load the module specified by this, get its
                    get_pipeline_definition function and add it to cache.

        Return:
            function: the get_pipeline_definition function of module specified
                      by loader.
        """
        logger.debug("starting")

        if loader:
            logger.debug("you set the pype loader to: %s", loader)
        else:
            loader = 'pypyr.pypeloaders.fileloader'
            logger.debug("use default pype loader: %s", loader)

        loader_function = self.get(loader, lambda: load_the_loader(loader))

        logger.debug("done")
        return loader_function


# global instance of the cache. use this to access the cache from elsewhere.
pypeloader_cache = PypeLoaderCache()


def load_the_loader(loader):
    """Loads the module specified by loader and returns its function.

    Args:
        loader: string: name of module to load

    Returns:
        function: the get_pipeline_definition function in the module
    """
    logger.debug("starting")

    # pipeline loading deliberately outside of try catch. The try catch
    # will try to run a failure-handler from the pipeline, but if the
    # pipeline doesn't exist there is no failure handler that can possibly
    # run so this is very much a fatal stop error.
    loader_module = pypyr.moduleloader.get_module(loader)

    try:
        get_pipeline_definition = getattr(
            loader_module, 'get_pipeline_definition'
        )
    except AttributeError:
        logger.error(
            "The pipeline loader %s doesn't have a "
            "get_pipeline_definition(pipeline_name, working_dir) "
            "function.",
            loader_module
        )
        raise

    logger.debug("loading the pipeline definition with %s", loader_module)
    logger.debug("%s done", loader_module)
    return get_pipeline_definition
