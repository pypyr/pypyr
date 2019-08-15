"""pypyr steps runner.

pipelinerunner uses this to parse and run steps.
"""

import logging
from pypyr.dsl import Step
from pypyr.errors import (ControlOfFlowInstruction,
                          Jump,
                          Stop,
                          StopStepGroup)

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class StepsRunner():
    """Run step-groups and steps.

    If you're wanting to run steps just like the pypyr cli does,
    run_step_groups() is a sensible entrypoint.
    """

    def __init__(self, pipeline_definition, context):
        """Initialize the Step Runner with the pipeline to maintain state.

        Args:
            pipeline_definition: pipeline yaml
            context: pypyr.context.Context. The pypyr context. Will mutate.
        """
        self.context = context
        self.pipeline = pipeline_definition

    def get_pipeline_steps(self, step_group):
        """Get the specified step-group's step from the pipeline.

        If there is no steps_group sequence on the pipeline, return None.
        Guess you could theoretically want to run a pipeline with nothing in
        it.

        Args:
            step_group: (str) Name of step-group

        Returns:
            Iterable collection of steps in the step-group.
        """
        logger.debug("starting")
        assert step_group

        logger.debug("retrieving %s steps from pipeline", step_group)
        if step_group in self.pipeline:
            steps = self.pipeline[step_group]

            if steps is None:
                logger.warning(
                    "%s: sequence has no elements. So it won't do anything.",
                    step_group,
                )
                logger.debug("done")
                return None

            steps_count = len(steps)

            logger.debug("%s steps found under %s in pipeline definition.",
                         steps_count, step_group)

            logger.debug("done")
            return steps
        else:
            logger.debug(
                "pipeline doesn't have a %(steps_group)s collection. Add a "
                "%(steps_group)s: sequence to the yaml if you want "
                "%(steps_group)s actually to do something.",
                {"steps_group": step_group}
            )
            logger.debug("done")
            return None

    def run_failure_step_group(self, group_name):
        """Run the group_name if it exists, as a failure handler..

        This function will swallow all errors, to prevent obfuscating the error
        condition that got it here to begin with.
        """
        logger.debug("starting")
        try:
            # if no group_name exists, it'll do nothing.
            self.run_step_group(group_name)
        except Exception as exception:
            logger.error("Failure handler also failed. Swallowing.")
            logger.error(exception)

        logger.debug("done")

    def run_pipeline_steps(self, steps):
        """Run the run_step(context) method of each step in steps.

        Args:
            steps: list. Sequence of Steps to execute
        """
        logger.debug("starting")
        assert isinstance(self.context, dict), (
            "context must be a dictionary, even if empty {}.")

        if steps is None:
            logger.debug("No steps found to execute.")
        else:
            step_count = 0

            for step in steps:
                step_instance = Step(step, self)
                step_instance.run_step(self.context)
                step_count += 1

            logger.debug("executed %s steps", step_count)

        logger.debug("done")

    def run_step_group(self, step_group_name):
        """Get the specified step group from the pipeline and run its steps."""
        logger.debug("starting %s", step_group_name)
        assert step_group_name

        steps = self.get_pipeline_steps(step_group=step_group_name)

        try:
            self.run_pipeline_steps(steps=steps)
        except Jump as jump:
            logger.debug("jump: jumping to %s", jump.groups)
            self.run_step_groups(groups=jump.groups,
                                 success_group=jump.success_group,
                                 failure_group=jump.failure_group)
            logger.debug("jump: done jumping to %s", jump.groups)
        except StopStepGroup:
            logger.debug("StopStepGroup: stopped %s", step_group_name)

        logger.debug("done %s", step_group_name)

    def run_step_groups(self, groups, success_group, failure_group):
        """Run stepgroups specified, with the success and failure handlers.

        Args:
            groups: (list) list of step-group names to run.
            success_group: (str) name of group to run on successful completion
                           of groups.
            failure_group: (str) name of group to run on error

        Returns:
            None
        """
        logger.debug("starting")

        if not groups:
            raise ValueError("you must specify which step-groups you want to "
                             "run. groups is None.")
        try:
            # run main steps
            for step_group in groups:
                self.run_step_group(step_group)

            # if nothing went wrong, run on_success
            if success_group:
                logger.debug(
                    "pipeline steps complete. Running %s steps now.",
                    success_group)
                self.run_step_group(success_group)
            else:
                logger.debug(
                    "pipeline steps complete. No success group specified.")
        except (ControlOfFlowInstruction, Stop):
            # Control-of-Flow/Stop are instructions to go somewhere
            # else, not errors per se.
            raise
        except Exception:
            # yes, yes, don't catch Exception. Have to, though, to run failure
            # handler. Also, it does raise it back up.
            if failure_group:
                logger.error(
                    "Something went wrong. Will now try to run %s.",
                    failure_group)

                # failure_step_group will log but swallow any errors
                self.run_failure_step_group(failure_group)
            else:
                logger.debug(
                    "Something went wrong. No failure group specified.")

            logger.debug("Raising original exception to caller.")
            raise

        logger.debug("done")
