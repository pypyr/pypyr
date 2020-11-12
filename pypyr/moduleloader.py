"""pypyr dynamic modules and path discovery.

Load modules dynamically, find things on file-system.

Attributes:
    working_dir (WorkingDir): Global shared current working dir.
"""

import importlib
import logging
from pathlib import Path
import sys
from pypyr.errors import PyModuleNotFoundError

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class WorkingDir():
    """The Working Directory.

    Call set_working_directory before you call get_working_directory.
    """

    def __init__(self):
        """Initialize cwd to None."""
        self._cwd = None

    def get_working_directory(self):
        """Get current working directory.

        Return:
            Path object for current working directory.

        Raises:
            ValueError: If set_working_directory wasn't called before this.
        """
        if not self._cwd:
            raise ValueError('working directory not set.')
        return self._cwd

    def set_working_directory(self, working_directory=None):
        """Add working_directory to sys.paths.

        Defaults to cwd if working_directory is None.

        This allows dynamic loading of arbitrary python modules in cwd.

        Args:
            working_directory: string. path to add to sys.paths

        """
        logger.debug("starting")

        if working_directory is None:
            working_directory = Path.cwd()

        logger.debug("adding %s to sys.paths", working_directory)
        # sys path doesn't accept Path
        sys.path.append(str(working_directory))
        self._cwd = Path(working_directory)

        logger.debug("done")


working_dir = WorkingDir()


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
        if err.name != module_abs_import:
            extended_msg = (
                f'error importing module {err.name} in {module_abs_import}')
            logger.error("Couldn't import module %s in this module: %s",
                         err.name,
                         module_abs_import)
        else:
            extended_msg = (
                f"{module_abs_import}.py should be in your working "
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


def get_working_directory():
    """Return current working directory as Path.

    Really just a convenience wrapper for
    moduleloader.working_dir.cwd
    """
    return working_dir.get_working_directory()


def set_working_directory(working_directory=None):
    """Add working_directory to sys.paths.

    Really just a convenience wrapper for
    moduleloader.working_dir.set_working_directory()

    This allows dynamic loading of arbitrary python modules in cwd.

    Args:
        working_directory: string. path to add to sys.paths

    """
    working_dir.set_working_directory(working_directory)
