"""pypyr pipeline runner.

Runs the pipeline specified by the input pipeline_name parameter.
Pipelines must have a "steps" list-like attribute.
"""
import pypyrcli.log.logger
import importlib
import os
import ruamel.yaml as yaml


pypyrcli.log.logger.set_logging_config()

logger = pypyrcli.log.logger.get_logger(__name__)


def get_module(module_abs_import):
    """Use importlib to get the module dynamically.

    Get instance of the module specified by the module_abs_import.
    This means that module_abs_import must be resolvable from this package.
    """
    logger.debug("starting")
    logger.debug(f"loading module {module_abs_import}")
    try:
        pipeline_module = importlib.import_module(module_abs_import)
        logger.debug("done")
        return pipeline_module
    except ModuleNotFoundError:
        logger.error(
            "The module doesn't exist. Looking for a file like this: "
            f"{module_abs_import}")
        raise


def get_parsed_context(pipeline, context):
    """Execute get_parsed_context handler if specified."""
    logger.debug("starting")

    if 'context_parser' in pipeline:
        parser_module_name = pipeline['context_parser']
        logger.debug(f"context parser found: {parser_module_name}")
        parser_module = get_module(parser_module_name)

        try:
            logger.debug(f"running parser {parser_module_name}")
            result_context = parser_module.get_parsed_context(context)
            logger.debug(f"step {parser_module_name} done")
            # Return context if it exists. If not, initialize to an empty
            # dictionary.
            return {} if result_context is None else result_context
        except AttributeError:
            logger.error(f"The parser {parser_module_name} doesn't have a "
                         "get_parsed_context(context) function.")
            raise
    else:
        logger.debug(
            "pipeline does not have custom context parser. Return None.")
        logger.debug("done")
        # initialize to an empty dictionary because you want to be able to run
        # with no context.
        return {}


def get_pipeline_definition(pipeline_name):
    """Open and parse the pipeline definition yaml.

    Get instance of the module specified by the pipeline_name.
    pipeline_name.yaml should be in the pipelines folder.
    """
    logger.debug("starting")
    logger.debug("loading pipeline definition")

    # look for name.yaml in the pipelines/ sub-directory
    logger.info(f"current directory is {os.getcwd()}")

    # looking for {cwd}/pipelines/[pipeline_name].yaml
    pipeline_path = os.path.abspath(os.path.join('pipelines',
                                                 pipeline_name + '.yaml'))

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


def get_pipeline_steps(pipeline, steps_group):
    """Get the steps attribute of module pipeline.

    If there is no steps sequence on the pipeline, return None. Guess you
    could theoretically want to run a pipeline with nothing in it.
    """
    logger.debug("starting")
    assert pipeline
    assert steps_group

    logger.debug(f"retrieving {steps_group} steps from pipeline")
    if steps_group in pipeline:
        steps = pipeline[steps_group]

        if steps is None:
            logger.warn(
                f"{steps_group}: sequence has no elements. So it won't do "
                "anything.")
            logger.debug("done")
            return None

        steps_count = len(steps)

        logger.debug(f"{steps_count} steps found under {steps_group} in "
                     "pipeline definition.")

        logger.debug("done")
        return pipeline[steps_group]
    else:
        logger.info(
            f"pipeline doesn't have a {steps_group} collection. Add a "
            f"{steps_group}: sequence to the yaml if you want {steps_group} "
            "actually to do something.")
        logger.debug("done")
        return None


def get_step_input_context(in_parameters, context):
    """Append step's 'in' parameters to context, if they exist.

    Append the [in] dictionary to the context. This will overwrite
    existing values if the same keys are already in there. I.e if
    in_parameters has {'eggs' : 'boiled'} and key 'eggs' already
    exists in context, context['eggs'] hereafter will be 'boiled'.

    Returns the new context dictionary.
    """
    logger.debug("starting")
    if in_parameters is not None:
        parameter_count = len(in_parameters)
        if parameter_count > 0:
            logger.debug(
                f"Updating context with {parameter_count} 'in' parameters.")
            context.update(in_parameters)

    logger.debug("done")
    return context


def main(pipeline_name, pipeline_context_input, log_level):
    """Entry point for pipeline runner."""
    pypyrcli.log.logger.log_level = log_level
    logger.setLevel(log_level)
    logger.debug("starting pipeline runner")

    logger.debug(f"you asked to run pipeline: {pipeline_name}")
    logger.debug(f"you set the initial context to: {pipeline_context_input}")

    pipeline_definition = get_pipeline_definition(pipeline_name=pipeline_name)

    try:
        # if parsed_context fails to assign, the failure hanlder will be unable
        # to run. View this as a dead-in-the-water irrecoverable input error.
        parsed_context = get_parsed_context(pipeline=pipeline_definition,
                                            context=pipeline_context_input)

        # run main steps
        context_out = run_step_group(pipeline_definition=pipeline_definition,
                                     step_group_name='steps',
                                     context=parsed_context)

        # if nothing went wrong, run on_success
        logger.debug("pipeline steps complete. Running on_success steps now.")
        run_step_group(pipeline_definition=pipeline_definition,
                       step_group_name='on_success', context=context_out)
    except Exception:
        # yes, yes, don't catch Exception. Have to, though, to run the failure
        # handler. Also, it does raise it back up.
        logger.error("Something went wrong. Will now try to run on_failure.")
        # use the input context, because context_out prob doesn't have a value
        # yet.
        run_failure_step_group(pipeline=pipeline_definition,
                               context=parsed_context)
        logger.error("Raising original exception to caller.")
        raise

    logger.debug("pipeline runner done")


def run_failure_step_group(pipeline, context):
    """Run the on_failure step group if it exists.

    This function will swallow all errors, to prevent obfuscating the error
    condition that got it here to begin with.
    """
    logger.debug("starting")
    context_out = context
    try:
        assert pipeline
        # if no on_failure exists, it'll do nothing.
        context_out = run_step_group(pipeline_definition=pipeline,
                                     step_group_name='on_failure',
                                     context=context)
    except Exception as exception:
        logger.error("Failure handler also failed. Swallowing.")
        logger.error(exception)
    logger.debug("done")
    return context_out


def run_pipeline_step(step_name, context):
    """Run a single pipeline step."""
    logger.debug("starting")
    logger.debug(f"running step {step_name}")

    step = get_module(step_name)

    try:
        logger.debug(f"running step {step}")
        result_context = step.run_step(context)
        assert result_context, (
            f"{step_name} returned None context. At the very least it must "
            "return an empty dictionary. Is the step super-sure it really "
            "wants to nuke the context for all subsequent steps? If not, add "
            "'return context' at the end of the step code.")
        logger.debug(f"step {step} done")
        return result_context
    except AttributeError:
        logger.error(f"The step {step_name} doesn't have a run_step(context) "
                     "function.")
        raise


def run_pipeline_steps(steps, context_input):
    """Run the run(context) method of each step in steps."""
    logger.debug("starting")
    assert isinstance(
        context_input, dict), "context must be a dictionary, even if empty {}."
    context = context_input

    if steps is None:
        logger.debug("No steps found to execute.")
    else:
        step_count = 0

        for step in steps:
            if isinstance(step, dict):
                logger.debug(f"{step} is complex.")
                step_name = step['name']

                context = get_step_input_context(step['in'], context)
            else:
                logger.debug(f"{step} is a simple string.")
                step_name = step

            context = run_pipeline_step(step_name=step_name,
                                        context=context)
            step_count += 1

        logger.debug(f"executed {step_count} steps")

    logger.debug("done")

    return context


def run_step_group(pipeline_definition, step_group_name, context):
    """Get the specified step group from the pipeline and run its steps."""
    logger.debug(f"starting {step_group_name}")
    assert step_group_name

    steps = get_pipeline_steps(pipeline=pipeline_definition,
                               steps_group=step_group_name)

    context_out = run_pipeline_steps(steps=steps, context_input=context)

    logger.debug(f"done {step_group_name}")

    return context_out
