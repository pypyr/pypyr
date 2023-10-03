"""PipelineDefinition and PipelineInfo classes.

A loader creates these. The PipelineDefinition holds the yaml payload of a
pipeline, and the PipelineInfo holds the pipeline metadata properties set by
the loader.

For the run-time arguments associated with a running pipeline, see
pypyr.pipeline.Pipeline instead.

All of the below could well be DataClasses + slots once py3.10 the min
supported version. Might be nice to have frozen class to make these hashable.
"""
from collections.abc import Mapping, Sequence
import logging
from typing import Self

from pypyr.dsl import Step
from pypyr.errors import (ControlOfFlowInstruction,
                          Jump,
                          PipelineDefinitionError,
                          Stop,
                          StopStepGroup)

logger = logging.getLogger(__name__)


class PipelineInfo():
    """The common attributes that every pipeline loader should set.

    Custom loaders that want to add more properties to a pipeline's meta-data
    should probably derive from this class.

    Attributes:
        pipeline_name (str): Name of pipeline, as set by the loader.
        loader (str): Absolute module name of the pipeline loader.
        parent (any): pipeline_name resolves from parent. The parent can be any
            type - it is up to the loader to interpret the parent property.
        is_loader_cascading (bool): Loader cascades to child pipelines if not
            otherwise set on pype. Default True.
        is_parent_cascading (bool): Parent cascades to child pipelines if not
            otherwise set on pype. Default True.
    """

    __slots__ = ['pipeline_name', 'loader', 'parent',
                 'is_loader_cascading', 'is_parent_cascading']

    def __init__(self, pipeline_name, loader, parent,
                 is_parent_cascading=True,
                 is_loader_cascading=True):
        """Initialize PipelineInfo.

        Args:
            pipeline_name (str): name of pipeline, as set by the loader.
            loader (str): absolute module name of pypeloader.
            parent (any): pipeline_name resolves from parent.
            is_loader_cascading (bool): Loader cascades to child pipelines if
                not otherwise set on pype. Default True.
            is_parent_cascading (bool): Parent cascades to child pipelines if
                not otherwise set on pype. Default True.
        """
        self.pipeline_name = pipeline_name
        self.loader = loader
        self.parent = parent
        self.is_loader_cascading = is_loader_cascading
        self.is_parent_cascading = is_parent_cascading

    def __eq__(self, other):
        """Check all instance attributes are equal."""
        type_self = type(self)

        if type_self is type(other):
            all_slots = [p for c in type_self.__mro__ for p in getattr(
                c, '__slots__', [])]
            return all(
                getattr(self, s, id(self)) == getattr(other, s, id(other))
                for s in all_slots)
        else:
            return False


class PipelineFileInfo(PipelineInfo):
    """Pipeline properties set by the default file loader.

    Loader and parent will cascade by default to child pipelines if not set
    otherwise on pypyr.steps.pype.

    Attributes:
        pipeline_name (str): Name of pipeline, as set by the loader.
        loader (str): Absolute module name of pypeloader.
        parent (Path): Path to the pipeline's parent directory on the
            file-system.
        path (Path): Path to the pipeline on the file system.
    """

    __slots__ = ['path']

    def __init__(self, pipeline_name, loader, parent, path):
        """Initialize PipelineFleInfo.

        Args:
            pipeline_name (str): name of pipeline, as set by the loader.
            loader (str): absolute module name of pypeloader.
            parent (Path): Path to the pipeline's parent directory on the
                file-system.
            path (Path): Path to the pipeline on the file system.
        """
        super().__init__(pipeline_name=pipeline_name,
                         loader=loader,
                         parent=parent)
        self.path = path


class PipelineBody():
    __slots__ = ['context_parser', 'step_groups']

    # region constructors
    def __init__(self,
                 context_parser: str | None = None,
                 step_groups: Mapping | None = None):
        self.context_parser: str | None = context_parser
        self.step_groups: Mapping | None = step_groups if step_groups else {}

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self:
        # if the pipeline is not a dict at top level, failures down-stream get
        # mysterious - this prevents malformed pipe from even making it into
        # cache.
        if not isinstance(mapping, Mapping):
            raise PipelineDefinitionError(
                "A pipeline must be a mapping at the top level. "
                "Does your top-level yaml have a 'steps:' key? "
                "For example:\n\n"
                "steps:\n"
                "  - name: pypyr.steps.echo\n"
                "    in:\n"
                "      echoMe: this is a bare bones pipeline example.\n")

        context_parser = None
        step_groups = {}
        for k, v in mapping.items():
            if k == 'context_parser':
                context_parser = v
                continue

            # v must be list-like
            if not isinstance(v, Sequence):
                raise PipelineDefinitionError(
                    "step group must be sequence/list.")
            else:
                if isinstance(v, (str, bytes, bytearray)):
                    raise PipelineDefinitionError(
                        "step group must be a list, not a string")

            step_groups[k] = [Step.from_step_definition(
                step_def) for step_def in v]

        return cls(context_parser=context_parser, step_groups=step_groups)

    # endregion constructors

    # region helpers to build pipeline in code rather than yaml
    def create_custom_step_group(self, name, steps: list[Step]) -> None:
        self.step_groups[name] = steps

    def create_steps_group(self, steps: list[Step]) -> None:
        # TODO: these defaults should prob come from config
        self.create_custom_step_group('steps', steps)

    def create_success_group(self, steps: list[Step]) -> None:
        self.create_custom_step_group('on_success', steps)

    def create_failure_group(self, steps: list[Step]) -> None:
        self.create_custom_step_group('on_failure', steps)

    def steps_append_step(self, step: Step) -> None:
        self.custom_step_group_append_step('steps', step)

    def success_append_step(self, step: Step) -> None:
        self.custom_step_group_append_step('on_success', step)

    def failure_append_step(self, step: Step) -> None:
        self.custom_step_group_append_step('on_failure', step)

    def custom_step_group_append_step(self, name, step: Step) -> None:
        if name not in self.step_groups:
            self.step_groups[name] = [step]
        else:
            self.step_groups[name].append(step)

    # endregion

    # region pipeline execution
    def get_pipeline_steps(self, step_group):
        """Get the specified step-group's steps from the pipeline.

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
        step_groups = self.step_groups
        if step_group in step_groups:
            steps = step_groups[step_group]

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

    def run_failure_step_group(self, group_name, context):
        """Run the group_name if it exists, as a failure handler..

        This function will swallow all errors, to prevent obfuscating the error
        condition that got it here to begin with.
        """
        logger.debug("starting")
        try:
            # if no group_name exists, it'll do nothing.
            self.run_step_group(group_name, context, raise_stop=True)
        except Stop:
            logger.debug("Stop instruction: done with failure handler %s.",
                         group_name)
            raise
        except Exception as exception:
            logger.error("Failure handler also failed. Swallowing.")
            logger.error(exception)

        logger.debug("done")

    def run_pipeline_steps(self, steps: Sequence[Step], context):
        """Run the run_step(context) method of each step in steps.

        Args:
            steps: list. Sequence of Steps to execute
        """
        logger.debug("starting")
        assert isinstance(context, dict), (
            "context must be a dictionary, even if empty {}.")

        if steps is None:
            logger.debug("No steps found to execute.")
        else:
            step_count = 0

            for step in steps:
                # step_instance = Step(step)
                # step_instance.run_step(self.context)
                step.run_step(context)
                step_count += 1

            logger.debug("executed %s steps", step_count)

        logger.debug("done")

    def run_step_group(self, step_group_name, context, raise_stop=False):
        """Get the specified step group from the pipeline and run its steps."""
        logger.debug("starting %s", step_group_name)
        assert step_group_name

        steps = self.get_pipeline_steps(step_group=step_group_name)

        try:
            self.run_pipeline_steps(steps=steps, context=context)
        except Jump as jump:
            logger.debug("jump: jumping to %s", jump.groups)
            self.run_step_groups(groups=jump.groups,
                                 success_group=jump.success_group,
                                 failure_group=jump.failure_group,
                                 context=context)
            logger.debug("jump: done jumping to %s", jump.groups)
        except StopStepGroup:
            logger.debug("StopStepGroup: stopped %s", step_group_name)
            if raise_stop:
                raise

        logger.debug("done %s", step_group_name)

    def run_step_groups(self, groups, success_group, failure_group, context):
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
                self.run_step_group(step_group, context=context)

            # if nothing went wrong, run on_success
            if success_group:
                logger.debug(
                    "pipeline steps complete. Running %s steps now.",
                    success_group)
                self.run_step_group(success_group, context=context)
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
            do_raise = True
            if failure_group:
                logger.error(
                    "Something went wrong. Will now try to run %s.",
                    failure_group)

                # failure_step_group will log but swallow any errors except
                # Stop. This so that pipeline can quit failure_handler
                # via stop without raising an error.
                try:
                    self.run_failure_step_group(failure_group, context=context)
                except StopStepGroup:
                    do_raise = False
            else:
                logger.debug(
                    "Something went wrong. No failure group specified.")

            if do_raise:
                logger.debug("Raising original exception to caller.")
                raise

        logger.debug("done")

    # endregion pipeline execution


class PipelineDefinition():
    """The pipeline body and its metadata.

    A loader creates the PipelineDefinition and sets the metadata in .info.

    The PipelineDefinition is a globally shared cache of the pipeline body &
    meta-data.

    Attributes:
        pipeline (dict-like): The pipeline yaml body.
        info (PipelineInfo): Meta-data set by the loader for the pipeline.
    """

    __slots__ = ['pipeline', 'info']

    def __init__(self, pipeline: PipelineBody, info: PipelineInfo):
        """Initialize a pipeline definition.

        Args:
            pipeline (dict-like): The pipeline yaml body itself.
            info (PipelineInfo): Meta-data set by the loader for the pipeline.
        """
        self.pipeline: PipelineBody = pipeline
        self.info: PipelineInfo = info

    def __eq__(self, other):
        """Equality comparison checks Pipeline and info objects are equal."""
        type_self = type(self)

        if type_self is type(other):
            all_slots = [p for c in type_self.__mro__ for p in getattr(
                c, '__slots__', [])]
            return all(
                getattr(self, s, id(self)) == getattr(other, s, id(other))
                for s in all_slots)
        else:
            return False
