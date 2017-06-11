"""pypyr step that runs another pipeline from within the current pipeline."""
import logging
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
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
                  context_parser - the equivalent to --context arg on the
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
     raise_error) = get_arguments(context)

    try:
        if use_parent_context:
            logger.info(f"pyping {pipeline_name}, using parent context.")
            pipelinerunner.run_pipeline(pipeline_name=pipeline_name,
                                        pipeline_context_input=pipe_arg,
                                        context=context,
                                        parse_input=not skip_parse)
        else:
            logger.info(f"pyping {pipeline_name}, without parent context.")
            pipelinerunner.run_pipeline(pipeline_name=pipeline_name,
                                        pipeline_context_input=pipe_arg,
                                        working_dir=context.working_dir,
                                        parse_input=not skip_parse)

        logger.info(f"pyped {pipeline_name}.")
    except Exception as ex_info:
        # yes, yes, don't catch Exception. Have to, though, in order to swallow
        # errs if !raise_error
        logger.error(f"Something went wrong pyping {pipeline_name}. "
                     f"{type(ex_info).__name__}: {ex_info}")

        if raise_error:
            logger.debug("Raising original exception to caller.")
            raise
        else:
            logger.debug(
                f"raiseError is False. Swallowing error in {pipeline_name}.")

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
               )

   Raises:
       pypyr.errors.KeyNotInContextError: if ['pype']['name'] is missing.
       pypyr.errors.KeyInContextHasNoValueError: if ['pype']['name'] exists but
                                                 is None.
    """
    context.assert_key_has_value(key='pype', caller=__name__)
    pype = context['pype']

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

    return (pipeline_name,
            use_parent_context,
            pipe_arg,
            skip_parse,
            raise_error)
