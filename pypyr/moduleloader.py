"""pypyr dynamic modules and path discovery.

Load modules dynamically, find things on file-system.
"""

import importlib
import logging
import sys
from pypyr.errors import PyModuleNotFoundError

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_module(module_abs_import):
    """Use importlib to get the module dynamically.

    Get instance of the module specified by the module_abs_import.
    This means that module_abs_import must be resolvable from this package.

    Args:
        module_abs_import: string. Absolute name of module to import.

    Raises:
        PyModuleNotFoundError: if module not found.

    """
    logger.debug("starting")
    logger.debug("loading module %s", module_abs_import)
    try:
        imported_module = importlib.import_module(module_abs_import)
        logger.debug("done")
        return imported_module
    except ModuleNotFoundError as err:
        extended_msg = (f"{module_abs_import}.py should be in your working "
                        "dir or it should be installed to the python path."
                        "\nIf you have 'package.sub.mod' your current working "
                        "dir should contain ./package/sub/mod.py\n"
                        "If you specified 'mymodulename', your current "
                        "working dir should contain ./mymodulename.py\n"
                        "If the module is not in your current working dir, it "
                        "must exist in your current python path - so you "
                        "should have run pip install or setup.py")
        logger.error("The module doesn't exist. "
                     "Looking for a file like this: %s",
                     module_abs_import)
        raise PyModuleNotFoundError(extended_msg) from err


def set_working_directory(working_directory):
    """Add working_directory to sys.paths.

    This allows dynamic loading of arbitrary python modules in cwd.

    Args:
        working_directory: string. path to add to sys.paths

    """
    logger.debug("starting")

    logger.debug("adding %s to sys.paths", working_directory)
    sys.path.append(working_directory)

    logger.debug("done")
