"""Context parser that returns a list from input arguments.

Takes input args (i.e separated by spaces on cli) and returns a list named
argList.

Where args are key=value pairs, returns a dictionary where each pair becomes a
dictionary element.

Don't have spaces in your values unless your really mean it. "k1=v1 ' k2'=v2"
will result in a context key name of ' k2' not 'k2'.

So cli input like this "ham eggs bacon drink=coffee", will yield context:
{ 'argList': ['ham', 'eggs', 'bacon'], 'drink': 'coffee'}
"""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Mapping
import logging

logger = logging.getLogger(__name__)

ARG_LIST_KEY = 'argList'


def get_parsed_context(args: list[str] | None) -> Mapping:
    """Create dict from combination of args & kwargs passed from cli.

    This supports the style of args that makefile does, i.e

    $ pypyr pipeline-name arg1 arg2 key1=value1 key2-"value 2"

    args go to context key `argList`. key=value pairs become context dictionary
    elements at root.

    Args:
      args: list of string. Passed from command-line invocation where:
            $ pypyr pipelinename this is the context_arg
            This would result in args == ['this', 'is', 'the', 'context_arg']

    Returns:
      dict. This dict will initialize the context for the pipeline run.
            The dict will have key `argList` with empty list [] if no args
            passed.
    """
    logger.debug("starting")
    if not args:
        logger.debug(
            "pipeline invoked without context arg set. For this\n"
            "argskwargs parser you're looking for something like:\n"
            "pypyr pipelinename arg1 arg2 k1=v1 k2=\"v 2\""
        )
        return {ARG_LIST_KEY: []}
    arg_list = []
    out: dict[str, str | list] = {}
    for a in args:
        # 1st = is separator, subsequent = just taken as part of the value
        key, sep, value = a.partition('=')
        if sep:
            out[key] = value
        else:
            arg_list.append(a)

    out[ARG_LIST_KEY] = arg_list

    return out
