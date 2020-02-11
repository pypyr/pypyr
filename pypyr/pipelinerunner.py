"""pypyr pipeline runner.

Runs the pipeline specified by the input pipeline_name parameter.
Pipelines must have a "steps" list-like attribute.

Attributes:
    pipeline_cache: global instance of the pipeline yaml cache.
                    Use this attribute to access the cache from elsewhere.
"""
import logging
import pypyr.context
import pypyr.log.logger
import pypyr.moduleloader
from pypyr.cache.parsercache import contextparser_cache
from pypyr.errors import Stop, StopPipeline
from pypyr.cache.pipelinecache import pipeline_cache
from pypyr.stepsrunner import StepsRunner
import pypyr.yaml

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_parsed_context(pipeline, context_in_args):
    """Execute get_parsed_context handler if specified.

    Dynamically load the module specified by the context_parser key in pipeline
    dict and execute the get_parsed_context function on that module.

    Args:
        pipeline: dict. Pipeline object.
        context_in_args: list of string. Input arguments from console.

    Returns:
        pypyr.context.Context() instance.

    Raises:
        AttributeError: parser specified on pipeline missing get_parsed_context
                        function.

    """
    logger.debug("starting")

    if 'context_parser' in pipeline:
        parser_module_name = pipeline['context_parser']
        logger.debug("context parser specified: %s", parser_module_name)
        get_parsed_context = contextparser_cache.get_context_parser(
            parser_module_name)

        logger.debug("running parser %s", parser_module_name)
        result_context = get_parsed_context(context_in_args)
        logger.debug("context parse %s done", parser_module_name)
        # Downstream steps likely to expect context not to be None, hence
        # empty rather than None.
        if result_context is None:
            logger.debug(
                "%s returned None. Using empty context instead",
                parser_module_name
            )
            return pypyr.context.Context()
        else:
            return pypyr.context.Context(result_context)
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
    groups=None,
    success_group=None,
    failure_group=None
):
    """Entry point for pypyr pipeline runner.

    Call this once per pypyr run. Call me if you want to run a pypyr pipeline
    from your own code. This function does some one-off 1st time initialization
    before running the actual pipeline.

    If you're invoking pypyr from your own application via the API,
    it's your responsibility to set up and configure logging. If you just want
    to replicate the log handlers & formatters that the pypyr cli uses, you can
    call pypyr.log.logger.set_root_logger() before invoking this function
    (pipelinerunner.main())

    Be aware that if you invoke this method, pypyr adds a NOTIFY - 25 custom
    log-level and notify() function to logging.

    pipeline_name.yaml should be in the working_dir/pipelines/ directory.

    Args:
        pipeline_name: string. Name of pipeline, sans .yaml at end.
        pipeline_context_input: string. Initialize the pypyr context with this
                                string.
        working_dir: path. looks for ./pipelines and modules in this directory.
        groups: list of str. step-group names to run in pipeline.
        success_group: str. step-group name to run on success completion.
        failure_group: str. step-group name to run on pipeline failure.

    Returns:
        None

    """
    pypyr.log.logger.set_up_notify_log_level()

    logger.debug("starting pypyr")

    # pipelines specify steps in python modules that load dynamically.
    # make it easy for the operator so that the cwd is automatically included
    # without needing to pip install a package 1st.
    pypyr.moduleloader.set_working_directory(working_dir)

    try:
        load_and_run_pipeline(pipeline_name=pipeline_name,
                              pipeline_context_input=pipeline_context_input,
                              groups=groups,
                              success_group=success_group,
                              failure_group=failure_group)
    except Stop:
        logger.debug("Stop: stopped pypyr")

    logger.debug("pypyr done")


def prepare_context(pipeline, context_in_args, context):
    """Prepare context for pipeline run.

    Args:
        pipeline: dict. Dictionary representing the pipeline.
        context_in_args: list of str. Args used to initialize context.
        context: pypyr.context.Context. Merge any new context generated from
                 context_in_string into this context instance.

    Returns:
        None. The context instance to use for the pipeline run is contained
              in the context arg, it's not passed back as a function return.

    """
    logger.debug("starting")

    parsed_context = get_parsed_context(
        pipeline=pipeline,
        context_in_args=context_in_args)

    context.update(parsed_context)

    logger.debug("done")


def load_and_run_pipeline(pipeline_name,
                          pipeline_context_input=None,
                          context=None,
                          parse_input=True,
                          loader=None,
                          groups=None,
                          success_group=None,
                          failure_group=None):
    """Load and run the specified pypyr pipeline.

    This function runs the actual pipeline by name. If you are running another
    pipeline from within a pipeline, call this, not main(). Do call main()
    instead for your 1st pipeline if there are pipelines calling pipelines.

    By default pypyr uses file loader. This means that pipeline_name.yaml
    should be in the working_dir/ directory if you're using fileloader.

    Look for pipelines and modules in the working_dir. Set the working_dir by
    calling pypyr.moduleloader.set_working_directory('/my/dir')

    Args:
        pipeline_name (str): Name of pipeline, sans .yaml at end.
        pipeline_context_input (str): Initialize the pypyr context with this
                                 string.
        context (pypyr.context.Context): Use if you already have a
                 Context object, such as if you are running a pipeline from
                 within a pipeline and you want to re-use the same context
                 object for the child pipeline. Any mutations of the context by
                 the pipeline will be against this instance of it.
        parse_input (bool): run context_parser in pipeline.
        loader (str): str. optional. Absolute name of pipeline loader module.
                If not specified will use pypyr.pypeloaders.fileloader.
        groups: list of str. step-group names to run in pipeline.
        success_group: str. step-group name to run on success completion.
        failure_group: str. step-group name to run on pipeline failure.

    Returns:
        None

    """
    logger.debug("you asked to run pipeline: %s", pipeline_name)

    logger.debug("you set the initial context to: %s", pipeline_context_input)

    if context is None:
        context = pypyr.context.Context()
        context.pipeline_name = pipeline_name
        context.working_dir = pypyr.moduleloader.get_working_directory()

    # pipeline loading deliberately outside of try catch. The try catch will
    # try to run a failure-handler from the pipeline, but if the pipeline
    # doesn't exist there is no failure handler that can possibly run so this
    # is very much a fatal stop error.
    pipeline_definition = pipeline_cache.get_pipeline(
        pipeline_name=pipeline_name,
        loader=loader)

    run_pipeline(
        pipeline=pipeline_definition,
        pipeline_context_input=pipeline_context_input,
        context=context,
        parse_input=parse_input,
        groups=groups,
        success_group=success_group,
        failure_group=failure_group
    )


def run_pipeline(pipeline,
                 context,
                 pipeline_context_input=None,
                 parse_input=True,
                 groups=None,
                 success_group=None,
                 failure_group=None):
    """Run the specified pypyr pipeline.

    This function runs the actual pipeline. If you are running another
    pipeline from within a pipeline don't call main(). Do call main()
    instead for your 1st pipeline, if there are subsequent pipelines calling
    pipelines use load_and_run_pipeline or run_pipeline.

    Pipeline and context should be already loaded. If pipeline not loaded yet,
    you probably want to call load_and_run_pipeline instead.

    If none of groups, success_group & failure_group specified, defaults to
    ['steps'], on_success, on_failure. If any of groups, success_group or
    failure_group specified, will ONLY run the specified (i.e if you specify
    groups you don't get on_success/on_failure groups unless you specify these
    explicitly.)

    Args:
        pipeline (dict): Dictionary representing the pipeline.
        context (pypyr.context.Context): Reusable context object.
        pipeline_context_input (str): Initialize the pypyr context with this
                                string.
        parse_input (bool): run context_parser in pipeline.
        groups: list of str. step-group names to run in pipeline.
        success_group: str. step-group name to run on success completion.
        failure_group: str. step-group name to run on pipeline failure.

    Returns:
        None

    """
    logger.debug("starting")

    if not groups:
        groups = ['steps']

        if not success_group and not failure_group:
            success_group = 'on_success'
            failure_group = 'on_failure'

    steps_runner = StepsRunner(pipeline_definition=pipeline, context=context)

    try:
        if parse_input:
            logger.debug("executing context_parser")
            prepare_context(pipeline=pipeline,
                            context_in_args=pipeline_context_input,
                            context=context)
        else:
            logger.debug("skipping context_parser")
    except Exception:
        # yes, yes, don't catch Exception. Have to, though, to run the failure
        # handler. Also, it does raise it back up.
        logger.error("Something went wrong. Will now try to run %s",
                     failure_group)

        # failure_step_group will log but swallow any errors
        steps_runner.run_failure_step_group(failure_group)
        logger.debug("Raising original exception to caller.")
        raise

    try:
        steps_runner.run_step_groups(groups=groups,
                                     success_group=success_group,
                                     failure_group=failure_group)
    except StopPipeline:
        logger.debug("StopPipeline: stopped %s", context.pipeline_name)
