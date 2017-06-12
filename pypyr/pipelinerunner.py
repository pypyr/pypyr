"""pypyr pipeline runner.

Runs the pipeline specified by the input pipeline_name parameter.
Pipelines must have a "steps" list-like attribute.
"""
import pypyr.context
import pypyr.log.logger
import pypyr.moduleloader
import pypyr.stepsrunner
import ruamel.yaml as yaml

# use pypyr logger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


def get_parsed_context(pipeline, context_in_string):
    """Execute get_parsed_context handler if specified.

    Dynamically load the module specified by the context_parser key in pipeline
    dict and execute the get_parsed_context function on that module.

    Args:
        pipeline: dict. Pipeline object.
        context_in_string: string. Argument string used to initialize context.

    Returns:
        pypyr.context.Context() instance.

    Raises:
        AttributeError: parser specified on pipeline missing get_parsed_context
                        function.
    """
    logger.debug("starting")

    if 'context_parser' in pipeline:
        parser_module_name = pipeline['context_parser']
        logger.debug(f"context parser found: {parser_module_name}")
        parser_module = pypyr.moduleloader.get_module(parser_module_name)

        try:
            logger.debug(f"running parser {parser_module_name}")
            result_context = parser_module.get_parsed_context(
                context_in_string)
            logger.debug(f"step {parser_module_name} done")
            # Downstream steps likely to expect context not to be None, hence
            # empty rather than None.
            if result_context is None:
                logger.debug(f"{parser_module_name} returned None. Using "
                             "empty context instead")
                return pypyr.context.Context()
            else:
                return pypyr.context.Context(result_context)
        except AttributeError:
            logger.error(f"The parser {parser_module_name} doesn't have a "
                         "get_parsed_context(context) function.")
            raise
    else:
        logger.debug("pipeline does not have custom context parser. Using "
                     "empty context.")
        logger.debug("done")
        # initialize to an empty dictionary because you want to be able to run
        # with no context.
        return pypyr.context.Context()


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

    pipeline_path = pypyr.moduleloader.get_pipeline_path(
        pipeline_name=pipeline_name,
        working_directory=working_dir)

    logger.debug(f"Trying to open pipeline at path {pipeline_path}")
    try:
        with open(pipeline_path) as yaml_file:
            pipeline_definition = yaml.safe_load(yaml_file)
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


def main(pipeline_name, pipeline_context_input, working_dir, log_level):
    """Entry point for pypyr pipeline runner.

    Call this once per pypyr run. Call me if you want to run a pypyr pipeline
    from your own code. This function does some one-off 1st time initialization
    before running the actual pipeline.

    pipeline_name.yaml should be in the working_dir/pipelines/ directory.

    Args:
        pipeline_name: string. Name of pipeline, sans .yaml at end.
        pipeline_context_input: string. Initialize the pypyr context with this
                                string.
        working_dir: path. looks for ./pipelines and modules in this directory.
        log_level: int. Standard python log level enumerated value.

    Returns:
        None
    """
    pypyr.log.logger.set_root_logger(log_level)

    logger.debug("starting pypyr")

    # pipelines specify steps in python modules that load dynamically.
    # make it easy for the operator so that the cwd is automatically included
    # without needing to pip install a package 1st.
    pypyr.moduleloader.set_working_directory(working_dir)

    run_pipeline(pipeline_name=pipeline_name,
                 pipeline_context_input=pipeline_context_input,
                 working_dir=working_dir)

    logger.debug("pypyr done")


def prepare_context(pipeline, context_in_string, context):
    """Prepare context for pipeline run.

    Args:
        pipeline: dict. Dictionary representing the pipeline.
        context_in_string: string. Argument string used to initialize context.
        context: pypyr.context.Context. Merge any new context generated from
                 context_in_string into this context instance.

    Returns:
        None. The context instance to use for the pipeline run is contained
              in the context arg, it's not passed back as a function return.
    """
    logger.debug("starting")

    parsed_context = get_parsed_context(
        pipeline=pipeline,
        context_in_string=context_in_string)

    context.update(parsed_context)

    logger.debug("done")


def run_pipeline(pipeline_name,
                 pipeline_context_input=None,
                 working_dir=None,
                 context=None,
                 parse_input=True):
    """Run the specified pypyr pipeline.

    This function runs the actual pipeline. If you are running another
    pipeline from within a pipeline, call this, not main(). Do call main()
    instead for your 1st pipeline if there are pipelines calling pipelines.

    pipeline_name.yaml should be in the working_dir/pipelines/ directory.

    Args:
        pipeline_name (str): Name of pipeline, sans .yaml at end.
        pipeline_context_input (str): Initialize the pypyr context with this
                                 string.
        working_dir (path): Look for pipelines and modules in this directory.
                     If context arg passed, will use context.working_dir and
                     ignore this argument. If context is None, working_dir
                     must be specified.
        context (pypyr.context.Context): Use if you already have a
                 Context object, such as if you are running a pipeline from
                 within a pipeline and you want to re-use the same context
                 object for the child pipeline. Any mutations of the context by
                 the pipeline will be against this instance of it.
        parse_input (bool): run context_parser in pipeline.

    Returns:
        None
    """
    logger.debug("starting")

    logger.debug(f"you asked to run pipeline: {pipeline_name}")
    logger.debug(f"you set the initial context to: {pipeline_context_input}")

    if context is None:
        context = pypyr.context.Context()
        context.working_dir = working_dir
    else:
        working_dir = context.working_dir

    # pipeline loading deliberately outside of try catch. The try catch will
    # try to run a failure-handler from the pipeline, but if the pipeline
    # doesn't exist there is no failure handler that can possibly run so this
    # is very much a fatal stop error.
    pipeline_definition = get_pipeline_definition(pipeline_name=pipeline_name,
                                                  working_dir=working_dir)

    try:
        if parse_input:
            logger.debug("executing context_parser")
            prepare_context(pipeline=pipeline_definition,
                            context_in_string=pipeline_context_input,
                            context=context)
        else:
            logger.debug("skipping context_parser")

        # run main steps
        pypyr.stepsrunner.run_step_group(
            pipeline_definition=pipeline_definition,
            step_group_name='steps',
            context=context)

        # if nothing went wrong, run on_success
        logger.debug("pipeline steps complete. Running on_success steps now.")
        pypyr.stepsrunner.run_step_group(
            pipeline_definition=pipeline_definition,
            step_group_name='on_success',
            context=context)
    except Exception:
        # yes, yes, don't catch Exception. Have to, though, to run the failure
        # handler. Also, it does raise it back up.
        logger.error("Something went wrong. Will now try to run on_failure.")

        # failure_step_group will log but swallow any errors
        pypyr.stepsrunner.run_failure_step_group(
            pipeline=pipeline_definition,
            context=context)
        logger.debug("Raising original exception to caller.")
        raise

    logger.debug("done")
