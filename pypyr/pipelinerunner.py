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
    """Execute get_parsed_context handler if specified."""
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

    Get instance of the module specified by the pipeline_name.
    pipeline_name.yaml should be in the pipelines folder.
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
    """Entry point for pipeline runner."""
    pypyr.log.logger.set_root_logger(log_level)

    logger.debug("starting pipeline runner")

    logger.debug(f"you asked to run pipeline: {pipeline_name}")
    logger.debug(f"you set the initial context to: {pipeline_context_input}")

    # pipelines specify steps in python modules that load dynamically.
    # make it easy for the operator so that the cwd is automatically included
    # without needing to pip install a package 1st.
    pypyr.moduleloader.set_working_directory(working_dir)

    pipeline_definition = get_pipeline_definition(pipeline_name=pipeline_name,
                                                  working_dir=working_dir)

    try:
        # if parsed_context fails to assign, the failure hanlder will be unable
        # to run. View this as a dead-in-the-water irrecoverable input error.
        parsed_context = get_parsed_context(
            pipeline=pipeline_definition,
            context_in_string=pipeline_context_input)

        # run main steps
        pypyr.stepsrunner.run_step_group(
            pipeline_definition=pipeline_definition,
            step_group_name='steps',
            context=parsed_context)

        # if nothing went wrong, run on_success
        logger.debug("pipeline steps complete. Running on_success steps now.")
        pypyr.stepsrunner.run_step_group(
            pipeline_definition=pipeline_definition,
            step_group_name='on_success',
            context=parsed_context)
    except Exception:
        # yes, yes, don't catch Exception. Have to, though, to run the failure
        # handler. Also, it does raise it back up.
        logger.error("Something went wrong. Will now try to run on_failure.")

        try:
            # parsed_context at the very least has to be defined before
            # run_failure_step_group will work and not cause another ref
            # before assignment err.
            parsed_context
        except NameError:
            parsed_context = {}

        # failure_step_group will log but swallow any errors
        pypyr.stepsrunner.run_failure_step_group(
            pipeline=pipeline_definition,
            context=parsed_context)
        logger.debug("Raising original exception to caller.")
        raise

    logger.debug("pipeline runner done")
