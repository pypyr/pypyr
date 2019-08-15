"""pypyr step that runs another pipeline from within the current pipeline."""
import logging
from pypyr.errors import (ControlOfFlowInstruction,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError,
                          Stop)
import pypyr.pipelinerunner as pipelinerunner

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Run another pipeline from this step.

    The parent pipeline is the current, executing pipeline. The invoked, or
    child pipeline is the pipeline you are calling from this step.

    Args:
        context: dictionary-like pypyr.context.Context. context is mandatory.
                 Uses the following context keys in context:
            - pype
                - name. mandatory. str. Name of pipeline to execute. This
                  {name}.yaml must exist in the working directory/pipelines
                  dir.
                - pipeArg. string. optional. String to pass to the
                  context_parser - the equivalent to context arg on the
                  pypyr cli. Only used if skipParse==False.
                - raiseError. bool. optional. Defaults to True. If False, log,
                  but swallow any errors that happen during the invoked
                  pipeline execution. Swallowing means that the current/parent
                  pipeline will carry on with the next step even if an error
                  occurs in the invoked pipeline.
                - skipParse. bool. optional. Defaults to True. skip the
                  context_parser on the invoked pipeline.
                - useParentContext. optional. bool. Defaults to True. Pass the
                  current (i.e parent) pipeline context to the invoked (child)
                  pipeline.
                - loader: str. optional. Absolute name of pipeline loader
                  module. If not specified will use
                  pypyr.pypeloaders.fileloader.
                - groups. list of str, or str. optional. Step-Groups to run in
                  pipeline. If you specify a str, will convert it to a single
                  entry list for you.
                - success. str. optional. Step-Group to run on successful
                  pipeline completion.
                - failure. str. optional. Step-Group to run on pipeline error.

    If none of groups, success & failure specified, will run the default pypyr
    steps, on_success & on_failure sequence.

    If groups specified, will only run groups, without a success or failure
    sequence, unless you specifically set these also.

    Returns:
        None

    Raises:
        pypyr.errors.KeyNotInContextError: if ['pype'] or ['pype']['name']
                                           is missing.
        pypyr.errors.KeyInContextHasNoValueError: ['pype']['name'] exists but
                                                  is empty.
    """
    logger.debug("started")

    (pipeline_name,
     use_parent_context,
     pipe_arg,
     skip_parse,
     raise_error,
     loader,
     step_groups,
     success_group,
     failure_group
     ) = get_arguments(context)

    try:
        if use_parent_context:
            logger.info("pyping %s, using parent context.", pipeline_name)
            pipelinerunner.load_and_run_pipeline(
                pipeline_name=pipeline_name,
                pipeline_context_input=pipe_arg,
                context=context,
                parse_input=not skip_parse,
                loader=loader,
                groups=step_groups,
                success_group=success_group,
                failure_group=failure_group
            )
        else:
            logger.info("pyping %s, without parent context.", pipeline_name)
            pipelinerunner.load_and_run_pipeline(
                pipeline_name=pipeline_name,
                pipeline_context_input=pipe_arg,
                parse_input=not skip_parse,
                loader=loader,
                groups=step_groups,
                success_group=success_group,
                failure_group=failure_group
            )

        logger.info("pyped %s.", pipeline_name)
    except (ControlOfFlowInstruction, Stop):
        # Control-of-Flow/Stop are instructions to go somewhere
        # else, not errors per se.
        raise
    except Exception as ex_info:
        # yes, yes, don't catch Exception. Have to, though, in order to swallow
        # errs if !raise_error
        logger.error("Something went wrong pyping %s. %s: %s",
                     pipeline_name, type(ex_info).__name__, ex_info)

        if raise_error:
            logger.debug("Raising original exception to caller.")
            raise
        else:
            logger.debug(
                "raiseError is False. Swallowing error in %s.", pipeline_name)

    logger.debug("done")


def get_arguments(context):
    """Parse arguments for pype from context and assign default values.

    Args:
        context: pypyr.context.Context. context is mandatory.

    Returns:
        tuple (pipeline_name, #str
               use_parent_context, #bool
               pipe_arg, #str
               skip_parse, #bool
               raise_error #bool
               groups #list of str
               success_group #str
               failure_group #str
               )

    Raises:
       pypyr.errors.KeyNotInContextError: if ['pype']['name'] is missing.
       pypyr.errors.KeyInContextHasNoValueError: if ['pype']['name'] exists but
                                                 is None.
    """
    context.assert_key_has_value(key='pype', caller=__name__)
    pype = context.get_formatted('pype')

    try:
        pipeline_name = pype['name']

        if pipeline_name is None:
            raise KeyInContextHasNoValueError(
                "pypyr.steps.pype ['pype']['name'] exists but is empty.")
    except KeyError as err:
        raise KeyNotInContextError(
            "pypyr.steps.pype missing 'name' in the 'pype' context item. "
            "You need to specify the pipeline name to run another "
            "pipeline.") from err

    use_parent_context = pype.get('useParentContext', True)
    pipe_arg = pype.get('pipeArg', None)
    skip_parse = pype.get('skipParse', True)
    raise_error = pype.get('raiseError', True)
    loader = pype.get('loader', None)
    groups = pype.get('groups', None)
    if isinstance(groups, str):
        groups = [groups]

    success_group = pype.get('success', None)
    failure_group = pype.get('failure', None)

    return (
        pipeline_name,
        use_parent_context,
        pipe_arg,
        skip_parse,
        raise_error,
        loader,
        groups,
        success_group,
        failure_group
    )
