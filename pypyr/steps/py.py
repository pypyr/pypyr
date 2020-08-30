"""pypyr step that executes a string as python.

Uses python's exec() to evaluate and execute arbitrary python code.
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Execute dynamic python code.

    Context is a dictionary or dictionary-like.
    Context must contain key 'pycode'
    Will exec context['pycode'] as dynamically interpreted python statements.

    context is mandatory. When you execute the pipeline, it should look
    something like this:
        pipeline-runner [name here] 'pycode=print(1+1)'.
    """
    logger.debug("started")
    context.assert_key_has_value(key='pycode', caller=__name__)

    logger.debug("Executing python string: %s", context['pycode'])
    locals_dictionary = locals()
    exec(context['pycode'], globals(), locals_dictionary)

    # It looks like this dance might be unnecessary in python 3.6
    logger.debug("looking for context update in exec")
    exec_context = locals_dictionary['context']
    context.update(exec_context)
    logger.debug("exec output context merged with pipeline context")

    logger.debug("done")
