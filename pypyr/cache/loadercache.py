"""Global cache for pypeloader modules.

Attributes:
    loader_cache: Global instance of the loader cache.
                  Use this attribute to access the cache from elsewhere.
"""
import logging
from pypyr.cache.cache import Cache
import pypyr.moduleloader
from pypyr.pipedef import PipelineDefinition, PipelineInfo

logger = logging.getLogger(__name__)


class Loader():
    """A single pipeline loader & the cache for all pipelines it has loaded.

    It loads pipelines using the get_pipeline_definition you assign to the
    loader at initialization.

    Attributes:
        name (str): Absolute module name of loader.
    """

    __slots__ = ['name', '_get_pipeline_definition', '_pipeline_cache']

    def __init__(self, name, get_pipeline_definition):
        """Initialize the loader and its pipeline cache.

        The expected function signature is:
        get_pipeline_definition(name: str,
                                parent: any) -> PipelineDefinition | Mapping

        Args:
            name: Absolute name of loader
            get_pipeline_definition: Reference to the function to call when
                loading a pipeline with this Loader.
        """
        self.name = name
        self._get_pipeline_definition = get_pipeline_definition
        self._pipeline_cache = Cache()

    def clear(self):
        """Clear all the pipelines in this Loader's cache."""
        self._pipeline_cache.clear()

    def get_pipeline(self, name, parent):
        """Get cached PipelineDefinition. Adds it to cache if it doesn't exist.

        The cache is local to this Loader instance.

        The combination of parent+name must be unique for this Loader. Parent
        should therefore have a sensible __str__ implementation because it
        forms part of the pipeline's identifying str key in the cache.

        Args:
            name (str): Name of pipeline, sans .yaml at end.
            parent (any): Parent in which to look for pipeline.

        Returns:
            pypyr.pipedef.PipelineDefinition: Yaml payload and loader info
                metadata for the pipeline.
        """
        # str keys perform better than tuples in dicts
        normalized_name = f'{parent}+{name}' if parent else name
        return self._pipeline_cache.get(
            normalized_name,
            lambda: self._load_pipeline(name, parent))

    def _load_pipeline(self, name, parent):
        """Execute get_pipeline_definition(name, parent) for this loader.

        If the loader get_pipeline_definition does not return a
        PipelineDefinition, this method will wrap the payload inside a
        PipelineDefinition for you.

        Args:
            name (str): Name of pipeline, sans .yaml at end.
            parent (any): Parent in which to look for pipeline.

        Returns:
            pypyr.pipedef.PipelineDefinition: Yaml payload and loader info
                metadata for the pipeline.
        """
        logger.debug("starting")

        logger.debug("loading the pipeline definition with %s", self.name)
        pipeline_definition = self._get_pipeline_definition(pipeline_name=name,
                                                            parent=parent)

        # loader can return either just the pipeline yaml payload itself, or a
        # PipelineDefinition wrapping both the pipeline yaml and its metadata.
        if not isinstance(pipeline_definition, PipelineDefinition):
            # standardize to the common cascading PipelineInfo if the loader
            # didn't provide any.
            pipeline_definition = PipelineDefinition(
                pipeline=pipeline_definition,
                info=PipelineInfo(pipeline_name=name,
                                  loader=self.name,
                                  parent=parent))
        logger.debug("done")
        return pipeline_definition


class LoaderCache(Cache):
    """Get Loader instances from the pypeloader cache."""

    def get_pype_loader(self, loader=None):
        """Get cached Loader instance.

        Defaults to pypyr.loaders.file if loader not specified.

        Load the module specified by this absolute name, get its
        get_pipeline_definition function, wrap it in a Loader instance, and add
        it to cache.

        Args:
            loader (str): Absolute name of loader to use.

        Returns:
            pypyr.loadercache.Loader: Loader with a pointer to the
                get_pipeline_definition function found in the module specified
                by the loader parameter.
        """
        logger.debug("starting")

        if loader:
            logger.debug("you set the pype loader to: %s", loader)
        else:
            loader = 'pypyr.loaders.file'
            logger.debug("use default pype loader: %s", loader)

        loader_instance = self.get(loader, lambda: load_the_loader(loader))

        logger.debug("done")
        return loader_instance

    def clear_pipes(self, loader_name=None):
        """Clear the pipeline cache.

        Args:
            loader_name (str): Clear pipelines for this loader. If not
                specified, will iterate all loaders in the loaders cache and
                clear each of their pipelines.
        """
        if loader_name:
            loader = self._cache.get(loader_name, None)
            if loader:
                loader.clear()
            else:
                logger.debug(
                    "%s not found in loader cache so there's nothing to clear",
                    loader_name)
        else:
            for _, loader in self._cache.items():
                loader.clear()


# global instance of the cache. use this to access the cache from elsewhere.
loader_cache = LoaderCache()


def load_the_loader(loader_name):
    """Load the module specified by loader and returns its function.

    Args:
        loader_name: string: name of module to load

    Returns:
        function: the get_pipeline_definition function in the module
    """
    logger.debug("starting")

    loader_module = pypyr.moduleloader.get_module(loader_name)

    try:
        get_pipeline_definition = getattr(loader_module,
                                          'get_pipeline_definition')
    except AttributeError:
        logger.error(
            "The pipeline loader %s doesn't have a "
            "get_pipeline_definition(pipeline_name, parent) "
            "function.",
            loader_module
        )
        raise

    loader = Loader(loader_name, get_pipeline_definition)
    logger.debug("%s done", loader_module)
    return loader
