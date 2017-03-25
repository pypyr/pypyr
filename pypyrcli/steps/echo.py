"""Step that echos simple input back to logger."""
import pypyrcli.log.logger

# logger means the log level will be set correctly
logger = pypyrcli.log.logger.get_logger(__name__)


def run_step(context):
    """Simple echo. Outputs context['echoMe'].

    Context is a dictionary or list-like.
    If context contains 'echoMe' will echo the value to logger. This could well
    be stdout.

    context is mandatory. When you execute the pipeline, it should look
    something like this: pipeline-runner [name here] --context 'schema,data'.
    """
    logger.debug("started")
    assert context, ("context must be set for echo. Did you set "
                     "--context 'echoMe=text here'?")

    logger.debug(context['echoMe'])

    logger.debug("done")
    return context
