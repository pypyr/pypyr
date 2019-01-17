"""pypyr pipeline runner.

Runs the pipeline specified by the input pipeline_name parameter.
Pipelines must have a "steps" list-like attribute.
"""
import logging
import pypyr.context
import pypyr.log.logger
import pypyr.moduleloader
import pypyr.stepsrunner
import pypyr.yaml

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


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


def main(
    pipeline_name,
    pipeline_context_input,
    working_dir,
    log_level,
    log_path,
):
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
        log_path: os.path. Append log to this path.

    Returns:
        None

    """
    pypyr.log.logger.set_root_logger(log_level, log_path)

    logger.debug("starting pypyr")

    # pipelines specify steps in python modules that load dynamically.
    # make it easy for the operator so that the cwd is automatically included
    # without needing to pip install a package 1st.
    pypyr.moduleloader.set_working_directory(working_dir)

    load_and_run_pipeline(pipeline_name=pipeline_name,
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


def load_and_run_pipeline(pipeline_name,
                          pipeline_context_input=None,
                          working_dir=None,
                          context=None,
                          parse_input=True,
                          loader=None):
    """Load and run the specified pypyr pipeline.

    This function runs the actual pipeline by name. If you are running another
    pipeline from within a pipeline, call this, not main(). Do call main()
    instead for your 1st pipeline if there are pipelines calling pipelines.

    By default pypyr uses file loader. This means that pipeline_name.yaml
    should be in the working_dir/pipelines/ directory.

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
        loader (str): str. optional. Absolute name of pipeline loader module.
                If not specified will use pypyr.pypeloaders.fileloader.

    Returns:
        None

    """
    logger.debug(f"you asked to run pipeline: {pipeline_name}")
    if loader:
        logger.debug(f"you set the pype loader to: {loader}")
    else:
        loader = 'pypyr.pypeloaders.fileloader'
        logger.debug(f"use default pype loader: {loader}")

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
    loader_module = pypyr.moduleloader.get_module(loader)

    try:
        get_pipeline_definition = getattr(
            loader_module, 'get_pipeline_definition'
        )
    except AttributeError:
        logger.error(
            f"The pipeline loader {loader_module} doesn't have a "
            "get_pipeline_definition(pipeline_name, working_dir) function.")
        raise

    logger.debug(f"loading the pipeline definition with {loader_module}")
    pipeline_definition = get_pipeline_definition(
        pipeline_name=pipeline_name,
        working_dir=working_dir
    )
    logger.debug(f"{loader_module} done")

    run_pipeline(
        pipeline=pipeline_definition,
        pipeline_context_input=pipeline_context_input,
        context=context,
        parse_input=parse_input
    )


def run_pipeline(pipeline,
                 context,
                 pipeline_context_input=None,
                 parse_input=True):
    """Run the specified pypyr pipeline.

    This function runs the actual pipeline. If you are running another
    pipeline from within a pipeline, call this, not main(). Do call main()
    instead for your 1st pipeline if there are pipelines calling pipelines.

    Pipeline and context should be already loaded.

    Args:
        pipeline (dict): Dictionary representing the pipeline.
        context (pypyr.context.Context): Reusable context object.
        pipeline_context_input (str): Initialize the pypyr context with this
                                string.
        parse_input (bool): run context_parser in pipeline.

    Returns:
        None

    """
    logger.debug("starting")

    try:
        if parse_input:
            logger.debug("executing context_parser")
            prepare_context(pipeline=pipeline,
                            context_in_string=pipeline_context_input,
                            context=context)
        else:
            logger.debug("skipping context_parser")

        # run main steps
        pypyr.stepsrunner.run_step_group(
            pipeline_definition=pipeline,
            step_group_name='steps',
            context=context)

        # if nothing went wrong, run on_success
        logger.debug("pipeline steps complete. Running on_success steps now.")
        pypyr.stepsrunner.run_step_group(
            pipeline_definition=pipeline,
            step_group_name='on_success',
            context=context)
    except Exception:
        # yes, yes, don't catch Exception. Have to, though, to run the failure
        # handler. Also, it does raise it back up.
        logger.error("Something went wrong. Will now try to run on_failure.")

        # failure_step_group will log but swallow any errors
        pypyr.stepsrunner.run_failure_step_group(
            pipeline=pipeline,
            context=context)
        logger.debug("Raising original exception to caller.")
        raise

    logger.debug("done")
