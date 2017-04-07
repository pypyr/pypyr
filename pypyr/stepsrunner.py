"""pypyr steps runner.

pipelinerunner uses this to parse and run steps.
"""

import pypyr.log.logger
import pypyr.moduleloader

# use pypyr logger to ensure loglevel is set correctly
logger = pypyr.log.logger.get_logger(__name__)


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
        logger.debug(
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

    step = pypyr.moduleloader.get_module(step_name)

    try:
        logger.debug(f"running step {step}")
        result_context = step.run_step(context)

        if context:
            # only ensure result is not empty if input wasn't empty. This is to
            # make sure step doesn't kill the context for downstream.
            assert (result_context), (
                f"{step_name} returned None context. At the very least it must"
                " return an empty dictionary. Is the step super-sure it really"
                " wants to nuke the context for all subsequent steps? If not,"
                " add 'return context' at the end of the step code.")
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
