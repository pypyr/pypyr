"""An instance of a running Pipeline.

This contains the run-time information of a pipeline and a reference
to the pipeline body itself (the PipelineDefinition).

Don't confuse this with PipelineDefinition. PipelineDefinition is the yaml
body & loader properties. The Pipeline is specific to a single running instance
of a pipeline, whereas the PipelineDefinition is shared by different Pipeline
instances.
"""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
import copy
import logging
from os import PathLike
from pathlib import Path

from pypyr.cache.loadercache import loader_cache
from pypyr.cache.parsercache import contextparser_cache
from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import Stop, StopPipeline, StopStepGroup
import pypyr.moduleloader
from pypyr.stepsrunner import StepsRunner

logger = logging.getLogger(__name__)


class Pipeline():
    """An instance of a running Pipeline.

    If you want to get pipeline properties from config.shortcuts if
    pipeline name matches a shortcut name, instantiate with the static factory
    Pipeline.new_pipe_and_args(). If you're not interested in
    config.shortcuts, you can instantiate with the default constructor instead.

    Use run() to run a pipeline. Use load_and_run_pipeline() to run a child
    pipeline from within an already running pipeline.

    If you specify py_dir, will add it to sys.path if it is not there already.

    Don't confuse a Pipeline with a PipelineDefinition. The Pipeline is the
    run-time properties of a single instance of a running pipeline, which
    includes the PipelineDefinition as a property. The PipelineDefinition is
    the pipeline yaml payload itself. A loader returns the PipelineDefinition.
    The PipelineDefinition is a globally shared cache of the pipeline body &
    meta-data.

    Attributes:
        name (str): Name of pipeline, sans .yaml at end.
        context_args (list[str]): All the input arguments after the pipeline
            name from cli.
        parse_input (bool): Default True. Run context_parser in pipeline.
        loader (str): Absolute name of pipeline loader module. If not specified
            will use pypyr.loaders.file.
        groups (list[str]): Step-group names to run in pipeline.
            Default if not set is ['steps'].
        success_group (str): Step-group name to run on success completion.
            Default if not set is on_success.
        failure_group (str: Step-group name to run on pipeline failure.
            Default if not set is on_failure.
        py_dir (Path-like): Custom python modules resolve from this dir.
        pipeline_definition (pypyr.pipedef.PipelineDefinition): The pipeline
            definition (its body/yaml payload) and loader information. Set by
            run(), not init.
        steps_runner (pypyr.stepsrunner.StepsRunner): StepsRunner instance that
            will run this pipeline's step-groups. Set by
            load_and_run_pipeline(), not init.
    """

    __slots__ = ['name', 'context_args', 'parse_input', 'loader', 'groups',
                 'success_group', 'failure_group', 'py_dir',
                 'pipeline_definition', 'steps_runner']

    # region constructors
    def __init__(self,
                 name: str,
                 context_args: list[str] | None = None,
                 parse_input: bool | None = True,
                 loader: str | None = None,
                 groups: list[str] | None = None,
                 success_group: str | None = None,
                 failure_group: str | None = None,
                 py_dir: str | bytes | PathLike | None = None) -> None:
        """Initialize a Pipeline.

        Args:
            name (str): Name of pipeline, sans .yaml at end.
            context_args (list[str]): All the input arguments after the
                pipeline name from cli.
            parse_input (bool): Default True. Run context_parser in pipeline.
            loader (str): Absolute name of pipeline loader module.
                        If not specified will use pypyr.loaders.file.
            groups (list[str]): Step-group names to run in pipeline.
                                Default if not set is ['steps'].
            success_group (str): Step-group name to run on success completion.
                                Default if not set is on_success.
            failure_group (str: Step-group name to run on pipeline failure.
                                Default if not set is on_failure.
            py_dir (Path-like): Custom python modules resolve from this dir.

        Returns:
            None
        """
        self.name = name
        self.context_args = context_args
        self.parse_input = parse_input
        self.loader = loader
        self.groups = groups
        self.success_group = success_group
        self.failure_group = failure_group
        self.py_dir = py_dir

        # initialize here, but use later
        # not using a classmethod fromLoader factory style thing coz PipeDef
        # AND StepsRunner depend on having a context object, which is subject
        # to logic only called later in obj life-time in load_and_run_pipeline.
        self.pipeline_definition = None
        self.steps_runner = None

    @classmethod
    def new_pipe_and_args(
        cls,
        name: str,
        context_args: list[str] | None = None,
        parse_input: bool | None = None,
        dict_in: dict | None = None,
        loader: str | None = None,
        groups: list[str] | None = None,
        success_group: str | None = None,
        failure_group: str | None = None,
        py_dir: str | bytes | PathLike | None = None) -> tuple[Pipeline,
                                                               dict | None]:
        """Return new Pipeline instance and dict_in args.

        Will initialize from config.shortcuts if arg `name` matches a shortcut.

        If shortcut doesn't exist fallback to the input args passed to new to
        initialize the Pipeline. If the shortcut does exist, any properties
        not specified by the shortcut configuration will fall back to this
        method's provided input arguments.

        When shortcut found, context_args will append to the end of
        `parser_args` as defined by shortcut. dict_in will merge into `args`
        as defined by shortcut.

        Returned Pipeline instance will default parse_input to True if
        shortcut.parser_args + context_args exist. If no context_args exist,
        but dict_in/shortcut.args do, returned Pipeline instance assumes
        parse_input=False if not explicitly set.

        Args:
            name (str): Name of pipeline, sans .yaml at end.
            context_args (list[str]): All the input arguments after the
                                      pipeline name from cli.
            parse_input (bool): Default True. Run context_parser in pipeline.
            dict_in (dict): Dict-like object to initialize the Context.
            loader (str): Absolute name of pipeline loader module.
                        If not specified will use pypyr.loaders.file.
            groups (list[str]): Step-group names to run in pipeline.
                                Default if not set is ['steps'].
            success_group (str): Step-group name to run on success completion.
                                Default if not set is on_success.
            failure_group (str: Step-group name to run on pipeline failure.
                                Default if not set is on_failure.
            py_dir (Path-like): Custom python modules resolve from this dir.

        Returns:
            New Pipeline instance, intialized from shortcut if name matches.
            Dict instance to use to initialize Context. This dict is the
            result of dict_in + input args found in shortcut, if any.
        """
        logger.debug("starting")
        if config.shortcuts:
            # assuming shortcuts is mostly empty dict, much faster to do truthy
            # if check before .get(), even though it looks redundant.
            shortcut = config.shortcuts.get(name)
            if shortcut:
                shortcut_name = name
                logger.debug("found shortcut in config for %s", shortcut_name)
                name = shortcut.get('pipeline_name')
                if not name:
                    raise pypyr.errors.ConfigError(
                        f"shortcut '{shortcut_name}' has no pipeline_name "
                        "set. You must set pipeline_name for this shortcut "
                        "in config so that pypyr knows which pipeline to run.")
                parser_args = shortcut.get('parser_args')
                if parser_args:
                    if isinstance(parser_args, str):
                        raise pypyr.errors.ConfigError(
                            f"shortcut '{shortcut_name}' parser_args should "
                            "be a list, not a string.")
                    # append context_args to shortcut's parser_args
                    context_args = (
                        parser_args + context_args if context_args
                        else parser_args)

                skip_parse = shortcut.get('skip_parse')
                # flip the bit - skip_parse means inverse of parse_args, but
                # only if it exists
                # since cli always set parse_args=True, the shortcut has
                # entirely to ignore the cli input to allow shortcut to calc
                # if parse_input should True/False based on args and
                # parser_args availability.
                parse_input = (
                    None if skip_parse is None else not skip_parse)

                shortcut_dict_in = shortcut.get('args')
                if shortcut_dict_in:
                    # deepcopy so downstream mutations don't touch the original
                    # dict in config
                    sc_dict = copy.deepcopy(shortcut_dict_in)
                    if dict_in:
                        # merge dict_in into shortcut's args
                        sc_dict.update(dict_in)
                    dict_in = sc_dict

                sc_groups = shortcut.get('groups', groups)
                # if config specified a str, take it to mean a single group
                groups = [sc_groups] if isinstance(sc_groups,
                                                   str) else sc_groups

                success_group = shortcut.get('success', success_group)
                failure_group = shortcut.get('failure', failure_group)
                loader = shortcut.get('loader', loader)
                dir_str = shortcut.get('py_dir')
                if dir_str:
                    # will still honor cwd for cli if not set, since it'll only
                    # override input if shortcut dir actually set.
                    py_dir = Path(dir_str)
            else:
                logger.debug("no shortcut found in config for %s", name)

        # if context_args exist, assume caller meant parse_input = True
        #  if no context_args but dict_in does exist, assume parse_input=False
        parse_input = cls._get_parse_input(parse_args=parse_input,
                                           args_in=context_args,
                                           dict_in=dict_in)
        pipeline = cls(name=name,
                       context_args=context_args,
                       parse_input=parse_input,
                       loader=loader,
                       groups=groups,
                       success_group=success_group,
                       failure_group=failure_group,
                       py_dir=py_dir)

        logger.debug("done")
        return pipeline, dict_in

    # endregion constructors

    def run(self, context: Context) -> None:
        """Run the current pypyr pipeline.

        Use me to run this pipeline.

        If you want to have the context available to you after the pipeline
        finishes, you (obviously) should provide an instance to the context
        parameter.

        Any exceptions raised from here indicate abnormal termination of a
        pipeline.

        Args:
            context (pypyr.context.Context): Any mutations of the context by
                the pipeline will be against this instance of it. If None, will
                create fresh new context with context_args using the pipeline's
                context_parser.

        Returns:
            None.
        """
        logger.debug("starting")

        try:
            self.load_and_run_pipeline(context)
        except Stop:
            logger.debug("Stop: stopped pypyr")

        logger.debug("done")

    def load_and_run_pipeline(self, context, parent=None):
        """Load and run the specified pypyr pipeline.

        Only use this from within an already running pipeline when it's
        calling a child pipeline.

        If you are running another pipeline from within a pipeline, call this,
        not run(). Do call run() instead for your 1st (root) pipeline if there
        are pipelines calling pipelines. The pypyr.steps.pype step uses
        load_and_run_pipeline to let pipelines call other pipelines.

        If you specify py_dir, will add it to sys.path if it is not there
        already.

        Args:
            context (pypyr.context.Context): Any mutations of the context by
                the pipeline will be against this instance of it. If None, will
                create fresh new context with context_args using the pipeline's
                context_parser.
            parent (Any): Passed to the loader. Can be anything of interest to
                the loader. In the case of the default file loader, this is
                a Path to the calling pipeline's parent directory.

        Returns:
            None.
        """
        logger.debug("you asked to run pipeline: %s", self.name)

        logger.debug("you set the initial context arg to: %s",
                     self.context_args)

        if context is None:
            context = Context()

        # add python module dir to sys.path before looking for loader
        if self.py_dir:
            pypyr.moduleloader.add_sys_path(self.py_dir)

        # could save loader_instance to self for >1 run on same pipeline, but
        # since you'd need extra check if self.loader has changed since last
        # time, O(1) dict lookup in cache prob not going to add too much
        # overhead by comparison.
        loader_instance = loader_cache.get_pype_loader(self.loader)

        # pipeline loading deliberately outside try catch. If the pipeline
        # doesn't exist there is no failure handler that can possibly run so
        # this is very much a fatal stop error.
        self.pipeline_definition = loader_instance.get_pipeline(name=self.name,
                                                                parent=parent)

        # add current pipeline's info to the callstack & remove when pipeline
        # done.
        with context.pipeline_scope(self):
            self._run_pipeline(context)

    def _run_pipeline(self, context):
        """Execute the internal implementation of the logic to run a pipeline.

        Don't call me unless you really know what you're doing - this method
        relies on setup done in the public method run() and
        load_and_run_pipeline().

        At this point the loader has already found and cached the
        PipelineDefinition, so this method is the actual runtime logic on the
        pipeline payload.

        context *must* be inside a pipeline_scope for this method to work
        as intended. pipeline_definition must be set on the current class
        instance.

        Args:
            context (pypyr.context.Context): Any mutations of the context by
                the pipeline will be against this instance of it. If None, will
                create fresh new context with context_args using the pipeline's
                context_parser.

        Returns:
            None.
        """
        logger.debug("starting")

        groups = self.groups
        success_group = self.success_group
        failure_group = self.failure_group

        if not groups:
            groups = [config.default_group]

            if not self.success_group and not self.failure_group:
                success_group = config.default_success_group
                failure_group = config.default_failure_group

        steps_runner = StepsRunner(
            pipeline_body=self.pipeline_definition.pipeline,
            context=context)

        self.steps_runner = steps_runner

        try:
            self._prepare_context(context)
        except Exception:
            # yes, yes, don't catch Exception. Have to, though, to run failure
            # handler. Also, it does raise it back up.
            logger.error("Something went wrong. Will now try to run %s",
                         failure_group)

            # failure_step_group will log but swallow any errors except Stop
            try:
                steps_runner.run_failure_step_group(failure_group)
            except StopStepGroup:
                pass

            logger.debug("Raising original exception to caller.")
            raise

        try:
            steps_runner.run_step_groups(groups=groups,
                                         success_group=success_group,
                                         failure_group=failure_group)
        except StopPipeline:
            logger.debug("StopPipeline: stopped %s", self.name)

        logger.debug("done")

    # region cli context input args
    def _prepare_context(self, context):
        """Prepare context for pipeline run.

        Args:
            context (pypyr.context.Context): Merge any new context generated
                from self.context_args by the pipeline's context_parser into
                this Context instance.

        Returns:
            None. The context instance passed in mutates, it's not passed back
            as a method return.
        """
        logger.debug("starting")

        if self.parse_input:
            logger.debug("executing context_parser")
            parsed_context = self._get_parsed_context()

            if parsed_context:
                context.update(parsed_context)
        else:
            logger.debug("skipping context_parser")

        logger.debug("done")

    def _get_parsed_context(self):
        """Execute get_parsed_context handler if specified.

        Dynamically load the module specified by the context_parser key in the
        pipeline dict and execute the get_parsed_context function on that
        module.

        Returns:
            dict-like instance, or None.

        Raises:
            AttributeError: parser specified on pipeline missing
                            get_parsed_context function.
        """
        logger.debug("starting")

        pipeline_yaml = self.pipeline_definition.pipeline
        parser_module_name = pipeline_yaml.get('context_parser')

        if parser_module_name:
            logger.debug("context parser specified: %s", parser_module_name)
            get_parsed_context = contextparser_cache.get_context_parser(
                parser_module_name)

            logger.debug("running parser %s", parser_module_name)

            result_dict = get_parsed_context(self.context_args)

            logger.debug("context parse %s done", parser_module_name)

            if result_dict is None:
                logger.debug(
                    "%s returned None. Using empty context instead",
                    parser_module_name
                )

            logger.debug("done")
            return result_dict
        else:
            logger.debug("pipeline does not have a context parser specified. "
                         "Initializing with empty context.")
            logger.debug("done")
            return None

    @staticmethod
    def _get_parse_input(parse_args, args_in, dict_in):
        """Return default for parse_input.

        This is to decide if context_parser should run or not.

        To make it easy on an API consumer, default behavior is ALWAYS to run
        parser UNLESS dict_in initializes context and there is no args_in.

        If dict_in specified, but no args_in: False
        If dict_in specified, AND args_in too: True
        If no dict_in specified, but args_in is: True
        If no dict_in AND no args_in: True
        If parse_args explicitly set, always honor its value.

        Args:
            parse_args (bool): Whether to run context parser.
            args_in (list[str]): String arguments as passed from the cli.
            dict_in (dict): Initialize context with this dict.

        Returns:
            Boolean. True if should parse input.
        """
        if parse_args is None:
            return not (not args_in and dict_in is not None)
        return parse_args
    # endregion cli context input args
