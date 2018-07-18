"""pypyr step that sets default values in context.

Sets values in context if they do not exist already. Does not overwrite
existing values. Supports nested hierarchies.

Example:
Given a context like this:
    key1: value1
    key2:
        key2.1: value2.1
    key3: None

And defaults input like this:
    key1: 'updated value here won't overwrite since it already exists'
    key2:
        key2.2: value2.2
    key3: 'key 3 exists so I won't overwrite

Will result in context:
    key1: value1
    key2:
        key2.1: value2.1
        key2.2: value2.2
    key3: None

By comparison, the in step decorator, contextset, contextsetf and contextmerge
overwrite values that are in context already.

Applies string interpolation as it adds. String interpolation applies to keys
and values.
"""
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Set hierarchy into context with substitutions if it doesn't exist yet.

    context is a dictionary or dictionary-like.
    context['defaults'] must exist. It's a dictionary.

    Will iterate context['defaults'] and add these as new values where
    their keys don't already exist. While it's doing so, it will leave
    all other values in the existing hierarchy untouched.

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
        defaults:
            key2: 'aaa_{key1}_zzz'
            key3:
                k33: value33
            key4: 'bbb_{key2}_yyy'

    This will result in return context:
        key1: value1
        key2: value2
        key3:
            k31: value31
            k32: value32
            k33: value33
        key4: bbb_value2_yyy
    """
    logger.debug("started")
    context.assert_key_has_value(key='defaults', caller=__name__)

    context.set_defaults(context['defaults'])

    logger.info(f"set {len(context['defaults'])} context item defaults.")

    logger.debug("done")
