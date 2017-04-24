"""Step that echos simple input back to logger."""
import pypyr.log.logger

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Simple echo. Outputs context['echoMe'].

    Context is a dictionary or dictionary-like.
    If context contains 'echoMe' will echo the value to logger. This could well
    be stdout.

    context is mandatory. When you execute the pipeline, it should look
    something like this: pipeline-runner [name here] --context 'echoMe=test'.
    """
    logger.debug("started")
    assert context, ("context must be set for echo. Did you set "
                     "--context 'echoMe=text here'?")

    val = context['echoMe'] if isinstance(
        context['echoMe'], str) else repr(context['echoMe'])

    logger.info(context.get_formatted_string(val))

    logger.debug("done")
