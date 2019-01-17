import logging
from pypyr.errors import PipelineNotFoundError
import pypyr.moduleloader
import pypyr.yaml
import os

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_pipeline_path(pipeline_name, working_directory):
    """Look for the pipeline in the various places it could be.

    First checks the cwd. Then checks pypyr/pipelines dir.

    Args:
        pipeline_name: string. Name of pipeline to find
        working_directory: string. Path in which to look for pipeline_name.yaml

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
        pypyr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.debug(f"pypyr installation directory is: {pypyr_dir}")
        pipeline_path = os.path.abspath(os.path.join(
            pypyr_dir,
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


def get_pipeline_definition(pipeline_name, working_dir):
    """Open and parse the pipeline definition yaml.

    Parses pipeline yaml and returns dictionary representing the pipeline.

    pipeline_name.yaml should be in the working_dir/pipelines/ directory.

    Args:
        pipeline_name: string. Name of pipeline. This will be the file-name of
                       the pipeline - i.e {pipeline_name}.yaml
        working_dir: path. Start looking in
                           ./working_dir/pipelines/pipeline_name.yaml

    Returns:
        dict describing the pipeline, parsed from the pipeline yaml.

    Raises:
        FileNotFoundError: pipeline_name.yaml not found in the various pipeline
                           dirs.

    """
    logger.debug("starting")

    pipeline_path = get_pipeline_path(
        pipeline_name=pipeline_name,
        working_directory=working_dir)

    logger.debug(f"Trying to open pipeline at path {pipeline_path}")
    try:
        with open(pipeline_path) as yaml_file:
            pipeline_definition = pypyr.yaml.get_pipeline_yaml(
                yaml_file)
            logger.debug(
                f"found {len(pipeline_definition)} stages in pipeline.")
    except FileNotFoundError:
        logger.error(
            "The pipeline doesn't exist. Looking for a file here: "
            f"{pipeline_name}.yaml in the /pipelines sub directory.")
        raise

    logger.debug("pipeline definition loaded")

    logger.debug("done")
    return pipeline_definition
