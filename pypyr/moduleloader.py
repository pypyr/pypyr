"""pypyr dynamic modules and path discovery.

Load modules dynamically, find things on file-system.
"""

import importlib
import os
from pypyr.errors import PipelineNotFoundError, PyModuleNotFoundError
import pypyr.log.logger
import sys


# use pypyr logger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


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
    logger.debug(f"loading module {module_abs_import}")
    try:
        imported_module = importlib.import_module(module_abs_import)
        logger.debug("done")
        return imported_module
    except ModuleNotFoundError as err:
        msg = ("The module doesn't exist. Looking for a file like this: "
               f"{module_abs_import}")

        extended_msg = (f"{module_abs_import}.py should be in your working "
                        "dir or it should be installed to the python path."
                        "\nIf you have 'package.sub.mod' your current working "
                        "dir should contain ./package/sub/mod.py\n"
                        "If you specified 'mymodulename', your current "
                        "working dir should contain ./mymodulename.py\n"
                        "If the module is not in your current working dir, it "
                        "must exist in your current python path - so you "
                        "should have run pip install or setup.py")
        logger.error(msg)
        raise PyModuleNotFoundError(extended_msg) from err


def get_pipeline_path(pipeline_name, working_directory):
    """Look for the pipeline in the various places it could be.

    First checks the cwd. Then checks pypyr/pipelines dir.

    Args:
        pipeline_name: string. Name of pipeline to find
        pipeline_name: string. Path in which to look for pipeline_name.yaml

    Returns:
        Absolute path to the pipeline_name.yaml file

    Raises:
        PipelineNotFoundError: if pipeline_name.yaml not found in working_dir
                               or in {pypyr install dir}/pipelines.
    """
    logger.debug("starting")

    # look for name.yaml in the pipelines/ sub-directory
    logger.debug(f"current directory is {working_directory}")

    # looking for {cwd}/pipelines/[pipeline_name].yaml
    pipeline_path = os.path.abspath(os.path.join(
        working_directory,
        'pipelines',
        pipeline_name + '.yaml'))

    if os.path.isfile(pipeline_path):
        logger.debug(f"Found {pipeline_path}")
    else:
        logger.debug(f"{pipeline_name} not found in current "
                     "directory/pipelines folder. Looking in pypyr install "
                     "directory instead.")
        pypyr_dir = os.path.dirname(os.path.abspath(__file__))
        logger.debug(f"pypyr installation directory is: {pypyr_dir}")
        pipeline_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'pipelines',
            pipeline_name + '.yaml'))

        if os.path.isfile(pipeline_path):
            logger.debug(f"Found {pipeline_path}")
        else:
            raise PipelineNotFoundError(f"{pipeline_name}.yaml not found in "
                                        f"either "
                                        f"{working_directory}/pipelines "
                                        f"or {pypyr_dir}/pipelines")

    logger.debug("done")
    return pipeline_path


def set_working_directory(working_directory):
    """Add working_directory to sys.paths.

    This allows dynamic loading of arbitrary python modules in cwd.

    Args:
        working_directory: string. path to add to sys.paths
    """
    logger.debug("starting")

    logger.debug(f"adding {working_directory} to sys.paths")
    sys.path.append(working_directory)

    logger.debug("done")
