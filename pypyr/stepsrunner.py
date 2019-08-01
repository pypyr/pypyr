"""pypyr steps runner.

pipelinerunner uses this to parse and run steps.
"""

import logging
from pypyr.dsl import Step

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


def get_pipeline_steps(pipeline, steps_group):
    """Get the steps attribute of module pipeline.

    If there is no steps sequence on the pipeline, return None. Guess you
    could theoretically want to run a pipeline with nothing in it.
    """
    logger.debug("starting")
    assert pipeline
    assert steps_group

    logger.debug("retrieving %s steps from pipeline", steps_group)
    if steps_group in pipeline:
        steps = pipeline[steps_group]

        if steps is None:
            logger.warning(
                "%s: sequence has no elements. So it won't do anything.",
                steps_group,
            )
            logger.debug("done")
            return None

        steps_count = len(steps)

        logger.debug("%s steps found under %s in pipeline definition.",
                     steps_count, steps_group)

        logger.debug("done")
        return steps
    else:
        logger.debug(
            "pipeline doesn't have a %(steps_group)s collection. Add a "
            "%(steps_group)s: sequence to the yaml if you want "
            "%(steps_group)s actually to do something.",
            {"steps_group": steps_group}
        )
        logger.debug("done")
        return None


def run_failure_step_group(pipeline, context):
    """Run the on_failure step group if it exists.

    This function will swallow all errors, to prevent obfuscating the error
    condition that got it here to begin with.
    """
    logger.debug("starting")
    try:
        assert pipeline
        # if no on_failure exists, it'll do nothing.
        run_step_group(pipeline_definition=pipeline,
                       step_group_name='on_failure',
                       context=context)
    except Exception as exception:
        logger.error("Failure handler also failed. Swallowing.")
        logger.error(exception)

    logger.debug("done")


def run_pipeline_steps(steps, context):
    """Run the run_step(context) method of each step in steps.

    Args:
        steps: list. Sequence of Steps to execute
        context: pypyr.context.Context. The pypyr context. Will mutate.
    """
    logger.debug("starting")
    assert isinstance(
        context, dict), "context must be a dictionary, even if empty {}."

    if steps is None:
        logger.debug("No steps found to execute.")
    else:
        step_count = 0

        for step in steps:
            step_instance = Step(step)
            step_instance.run_step(context)
            step_count += 1

        logger.debug("executed %s steps", step_count)

    logger.debug("done")


def run_step_group(pipeline_definition, step_group_name, context):
    """Get the specified step group from the pipeline and run its steps."""
    logger.debug("starting %s", step_group_name)
    assert step_group_name

    steps = get_pipeline_steps(pipeline=pipeline_definition,
                               steps_group=step_group_name)

    run_pipeline_steps(steps=steps, context=context)

    logger.debug("done %s", step_group_name)
