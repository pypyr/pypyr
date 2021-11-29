"""Load pipelines from the filesystem."""
import logging
from pathlib import Path

from pypyr.cache.cache import Cache
from pypyr.errors import PipelineNotFoundError
from pypyr.moduleloader import add_sys_path, CWD
from pypyr.pipedef import PipelineDefinition, PipelineFileInfo
import pypyr.yaml

logger = logging.getLogger(__name__)


_file_cache = Cache()
cwd_pipelines_dir = CWD.joinpath('pipelines')
pypyr_dir = Path(__file__).parents[1]
builtin_pipelines_dir = pypyr_dir.joinpath('pipelines')


# region find pipeline path
def find_pipeline(file_name, dirs):
    """Look for file_name in dirs.

    Args:
        file_name (str): String, likely {pipeline_name}.yaml
        dirs (list[(Path, str)]): List of (dir, msg). Msg prints
            to debug output if not found in this path.

    Returns:
        Resolved Path instance if found.

    Raises:
        PipelineNotFoundError: file_name not found in any of the dirs.
    """
    for parent in dirs:
        parent_dir = parent[0]
        path = parent_dir.joinpath(file_name)

        if path.is_file():
            logger.debug("Found %s", path)
            break
        else:
            logger.debug(parent[1], file_name)
    else:
        # didn't hit a break means no pipeline found anywhere
        searched_locations = "\n".join([str(p[0]) for p in dirs])
        raise PipelineNotFoundError(
            f"{file_name} not found in any of the following:\n"
            f"{searched_locations}")

    return path.resolve()


def get_pipeline_path(pipeline_name, parent):
    """Look for the pipeline in the various places it could be.

    1. If absolute path, just check that
    2. Check in parent, if it's specified
    3. Checks the cwd, if it's not the same as parent (2)
    4. Then check cwd/pipelines
    5. Then check {pypyr install dir}/pipelines dir.

    Args:
        pipeline_name (str): Name of pipeline to find
        parent (Path): 1st Path in which to look for pipeline_name.yaml

    Returns:
        Absolute Path to the pipeline_name.yaml file

    Raises:
        PipelineNotFoundError: if pipeline_name.yaml not anywhere.
    """
    logger.debug("starting")

    logger.debug("current parent is %s", parent)

    search_locations = []
    file_name = f'{pipeline_name}.yaml'

    # 1. absolute paths
    abs_candidate = Path(file_name)
    if abs_candidate.is_absolute():
        if abs_candidate.is_file():
            logger.debug("Found %s", abs_candidate)
            logger.debug("done")
            return abs_candidate.resolve()
        else:
            raise PipelineNotFoundError(f"{abs_candidate} does not exist.")
    else:
        # 2. parent/{pipeline_name}.yaml: go to 2 if parent == cwd
        if parent:
            parent = parent if isinstance(parent, Path) else Path(parent)
            # do a resolve so that full path in searched_locations err msg.
            parent = parent.resolve()
            # samefile raises err if either path doesn't .exist
            if parent.exists():
                if not parent.samefile(CWD):
                    search_locations.append((
                        parent,
                        "%s not found in parent pipeline directory. "
                        "Looking in cwd instead."))
            else:
                logger.debug(
                    'parent dir %s does not exist. skipping to cwd look-up.',
                    parent)

        # 3. {cwd}/{pipeline_name}.yaml
        search_locations.append((CWD,
                                "%s not found in cwd. "
                                 "Looking in 'cwd/pipelines' instead."))

        # 4. {cwd}/pipelines/{pipeline_name}.yaml
        search_locations.append((cwd_pipelines_dir,
                                "%s not found in cwd/pipelines. "
                                 "Looking in pypyr install directory instead.")
                                )

        # 5. {pypyr dir}/pipelines/{pipeline_name}.yaml
        search_locations.append((builtin_pipelines_dir,
                                "%s not found in {pypyr-dir}/pipelines."))

        pipeline_path = find_pipeline(file_name, search_locations)
        logger.debug("done")
        return pipeline_path

# endregion find pipeline path


def get_pipeline_definition(pipeline_name, parent):
    """Open and parse the pipeline definition yaml.

    Finds the yaml file, parses the yaml and returns a PipelineDefinition.

    pipeline_name.yaml should be in the parent/ directory, or in the
    fileloader directory look-up sequence.

    Args:
        pipeline_name (str): Name of pipeline. This will be the file-name of
                             the pipeline - i.e {pipeline_name}.yaml
        parent (Path-like): Start looking in parent/pipeline_name.yaml

    Returns:
        PipelineDefinition describing the pipeline. The dict parsed from the
            pipeline yaml is in its .pipeline property.
    """
    logger.debug("starting")

    pipeline_path = get_pipeline_path(pipeline_name=pipeline_name,
                                      parent=parent)

    logger.debug("Trying to open pipeline at path %s", pipeline_path)

    pipeline_definition = _file_cache.get(
        pipeline_path,
        lambda: load_pipeline_from_file(pipeline_path))

    logger.debug("found %d stages in pipeline.",
                 len(pipeline_definition.pipeline))

    logger.debug("done")
    return pipeline_definition


def load_pipeline_from_file(path):
    """Load pipeline yaml from path on disk.

    Initialize a PipelineFileInfo for the pipeline with file loader specific
    properties.

    Args:
        path (Path-like): path to pipeline

    Returns:
        PipelineDefinition describing the pipeline, parsed from the yaml file
            at path.

    Raises:
        FileNotFoundError: path not found.
    """
    logger.debug("starting")

    try:
        with open(path) as yaml_file:
            pipeline_yaml = pypyr.yaml.get_pipeline_yaml(yaml_file)
    except FileNotFoundError:
        # this can only happen if file disappears between get_pipeline_path
        # & here, so pretty edge
        logger.error(
            "Couldn't open the pipeline. Looking for a file here: %s", path)
        raise

    # since path itself resolved, parent also already resolved.
    parent_dir = path.parent

    add_sys_path(parent_dir)

    info = PipelineFileInfo(pipeline_name=path.name,
                            parent=parent_dir,
                            loader=__name__,
                            path=path)

    pipeline_definition = PipelineDefinition(pipeline=pipeline_yaml,
                                             info=info)

    logger.debug("done")
    return pipeline_definition
