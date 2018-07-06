"""pypyr step that merges the input mappings into context.

Whereas contextset and contextsetf overwrites values that are in context
already, contextmerge merges its input into context, preserving the existing
hierarchy while just updating the values where specified in the contextmerge
input.

Applies string interpolation as it merges. String interpolation applies to keys
and values.
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Merge hierarchy into context with substitutions.

    context is a dictionary or dictionary-like.
    context['contextMerge'] must exist. It's a dictionary.

    Will iterate context['contextMerge'] and save the values as new keys to the
    context where they exist already, and add these as new values where they
    don't already exist. While it's doing so, it will leave unspecified values
    in the existing hierarchy untouched.

    List merging is purely additive, with no checks for uniqueness or already
    existing list items. E.g context [0,1,2] with contextMerge=[2,3,4]
    will result in [0,1,2,2,3,4]

    Keep this in mind especially where complex types like
    dicts nest inside a list - a merge will always add a new dict list item,
    not merge it into whatever dicts might exist on the list already.

    For example, say input context is:
        key1: value1
        key2: value2
        key3:
            k31: value31
            k32: value32
        contextMerge:
            key2: 'aaa_{key1}_zzz'
            key3:
                k33: value33
            key4: 'bbb_{key2}_yyy'

    This will result in return context:
        key1: value1
        key2: aaa_value1_zzz
        key3:
            k31: value31
            k32: value32
            k33: value33
        key4: bbb_value2_yyy
    """
    logger.debug("started")
    context.assert_key_has_value(key='contextMerge', caller=__name__)

    context.merge(context['contextMerge'])

    logger.info(f"merged {len(context['contextMerge'])} context items.")

    logger.debug("done")
