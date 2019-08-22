import logging
from pathlib import Path
from pypyr.errors import PipelineNotFoundError
import pypyr.moduleloader
import pypyr.yaml

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_pipeline_path(pipeline_name, working_directory):
    """Look for the pipeline in the various places it could be.

    First checks the cwd
    Then check cwd/pipelines
    Then checks {pypyr install dir}/pipelines dir.

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
    logger.debug("current directory is %s", working_directory)

    cwd = Path(working_directory)

    # look for cwd/{pipeline_name}.yaml
    pipeline_path = cwd.joinpath(f'{pipeline_name}.yaml')

    if pipeline_path.is_file():
        logger.debug("Found %s", pipeline_path)
    else:
        logger.debug("%s not found in working directory. "
                     "Looking in '{working dir}/pipelines' instead.",
                     pipeline_name)
        # looking for {cwd}/pipelines/[pipeline_name].yaml
        pipeline_path = cwd.joinpath('pipelines',
                                     f'{pipeline_name}.yaml').resolve()

        if pipeline_path.is_file():
            logger.debug("Found %s", pipeline_path)
        else:
            logger.debug("%s not found in working directory/pipelines folder. "
                         "Looking in pypyr install directory instead.",
                         pipeline_name)
            pypyr_dir = Path(__file__).resolve().parents[1]
            logger.debug("pypyr installation directory is: %s", pypyr_dir)
            pipeline_path = pypyr_dir.joinpath('pipelines',
                                               f'{pipeline_name}.yaml')

            if pipeline_path.is_file():
                logger.debug("Found %s", pipeline_path)
            else:
                raise PipelineNotFoundError(
                    f"{pipeline_name}.yaml not found in any of the "
                    "following:\n"
                    f"{working_directory}\n"
                    f"{working_directory}/pipelines\n"
                    f"{pypyr_dir}/pipelines")

    logger.debug("done")
    return pipeline_path


def get_pipeline_definition(pipeline_name, working_dir):
    """Open and parse the pipeline definition yaml.

    Parses pipeline yaml and returns dictionary representing the pipeline.

    pipeline_name.yaml should be in the working_dir/ directory, or in the
    fileloader directory look-up sequence.

    Args:
        pipeline_name: string. Name of pipeline. This will be the file-name of
                       the pipeline - i.e {pipeline_name}.yaml
        working_dir: path. Start looking in
                           ./working_dir/pipeline_name.yaml

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

    logger.debug("Trying to open pipeline at path %s", pipeline_path)
    try:
        with open(pipeline_path) as yaml_file:
            pipeline_definition = pypyr.yaml.get_pipeline_yaml(
                yaml_file)
            logger.debug(
                "found %d stages in pipeline.", len(pipeline_definition))
    except FileNotFoundError:
        logger.error(
            "The pipeline doesn't exist. Looking for a file here: "
            "%s", pipeline_path)
        raise

    logger.debug("pipeline definition loaded")

    logger.debug("done")
    return pipeline_definition
