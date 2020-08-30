"""Global cache for run_step functions of Steps.

Attributes:
    step_cache: global instance of the context_parser cache.
                      Use this attribute to access the cache from elsewhere.
"""
import logging
from pypyr.cache.cache import Cache
import pypyr.moduleloader

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class StepCache(Cache):
    """Get functions from the Step cache."""

    def get_step(self, step_name):
        """Get cached run_step function. Adds to cache if not exist.

        Args:
            step_name: load the step module specified by this, get its
                       run_step function and add it to cache.

        Return:
            function: the run_step function of module specified by step_name.
        """
        logger.debug("starting")

        runstep_function = self.get(step_name,
                                    lambda: load_the_step(step_name))

        logger.debug("done")
        return runstep_function


# global instance of the cache. use this to access the cache from elsewhere.
step_cache = StepCache()


def load_the_step(step_name):
    """Load the module specified by step_name, returns its function.

    Args:
        step_name: (string) name of Step module to load

    Returns:
        function: the run_step function in the module
    """
    logger.debug("starting")

    step_module = pypyr.moduleloader.get_module(step_name)
    logger.debug("step module loaded: %s", step_module)

    try:
        run_step_function = getattr(step_module, 'run_step')
    except AttributeError:
        logger.error("The step %s in module %s "
                     "doesn't have a run_step(context) function.",
                     step_name, step_module)
        raise
    logger.debug("done")

    return run_step_function
