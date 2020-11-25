"""pypyr step that executes a string as python.

Uses python's exec() to evaluate and execute arbitrary python code.
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Execute dynamic python code.

    Takes two forms of input:
        py: exec contents as dynamically interpreted python statements, with
            contents of context available as vars.
        pycode: exec contents as dynamically interpreted python statements,
            with the context object itself available as a var.

    Args:
        context (pypyr.context.Context): Mandatory.
            Context is a dictionary or dictionary-like.
            Context must contain key 'py' or 'pycode'
    """
    logger.debug("started")

    if 'pycode' in context:
        exec_pycode(context)
    else:
        context.assert_key_has_value(key='py', caller=__name__)
        exec(context['py'], {}, context)

    logger.debug("exec output context merged with pipeline context")

    logger.debug("done")


def exec_pycode(context):
    """Exec contents of pycode.

    This form of execute means pycode does not have the contents of context in
    the locals() namespace, so referencing context needs to do:
        a = context['myvar']

    Rather than just
        a = myvar

    Args:
        context (pypyr.context.Content): context containing `pycode` key.

    Returns:
        None. Any mutations to content is on the input arg instance itself.
    """
    context.assert_key_has_value(key='pycode', caller=__name__)
    logger.debug("Executing python string: %s", context['pycode'])
    locals_dictionary = locals()
    exec(context['pycode'], globals(), locals_dictionary)

    # It looks like this dance might be unnecessary in python 3.6
    logger.debug("looking for context update in exec")
    exec_context = locals_dictionary['context']
    context.update(exec_context)
