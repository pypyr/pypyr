"""pypyr dynamic modules and path discovery.

Load modules dynamically, find things on file-system.
"""

import pypyr.log.logger
import importlib

logger = pypyr.log.logger.get_logger(__name__)


def get_module(module_abs_import):
    """Use importlib to get the module dynamically.

    Get instance of the module specified by the module_abs_import.
    This means that module_abs_import must be resolvable from this package.
    """
    logger.debug("starting")
    logger.debug(f"loading module {module_abs_import}")
    try:
        pipeline_module = importlib.import_module(module_abs_import)
        logger.debug("done")
        return pipeline_module
    except ModuleNotFoundError:
        logger.error(
            "The module doesn't exist. Looking for a file like this: "
            f"{module_abs_import}")
        raise
