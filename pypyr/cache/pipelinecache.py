"""Global cache for pipeline yaml.

Attributes:
    pipeline_cache: global instance of the pipeline yaml cache.
                    Use this attribute to access the cache from elsewhere.
"""
import logging
from pypyr.cache.cache import Cache
from pypyr.cache.loadercache import pypeloader_cache
import pypyr.moduleloader

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class PipelineCache(Cache):
    """Get and add Pipeline yaml from the pipelines cache."""

    def get_pipeline(self, pipeline_name, loader=None):
        """Get cached pipeline yaml. Adds to cache if not exist.

        Args:
            pipeline_name: (string) Name of pipeline, sans .yaml at end.
            loader: (string) Name of loader to load the pipeline

        Returns:
            yaml: Yaml representation of pipeline_name
        """
        logger.debug("starting")
        pipeline = self.get(pipeline_name, load_pipeline(pipeline_name,
                                                         loader))

        logger.debug("done")
        return pipeline


# single global instance of pipelines in a cache
pipeline_cache = PipelineCache()


def load_pipeline(pipeline_name, loader=None):
    """Return function that loads the pipeline using loader.

    This is a wrapped function, so it returns a callable. The actual work
    happens in the inner function.

    Args:
        pipeline_name (str): Name of pipeline, sans .yaml at end.
        loader (str): str. optional. Absolute name of pipeline loader module.
                If not specified will use pypyr.pypeloaders.fileloader.

    Returns:
        callable that will execute the loader and retrieve the pipeline def.
    """
    def load_pipeline_inner():
        logger.debug("starting")

        get_pipeline_definition = pypeloader_cache.get_pype_loader(loader)

        pipeline_definition = get_pipeline_definition(
            pipeline_name=pipeline_name,
            working_dir=pypyr.moduleloader.get_working_directory()
        )
        logger.debug("done")
        return pipeline_definition

    return load_pipeline_inner
