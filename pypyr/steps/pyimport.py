"""pypyr step that imports to the namespace for PyString.

Make Python stdlib or your own code available to any PyString in the pipeline.

Only supports absolute imports, not relative.

Supports python import syntax like:
    import x
    import x as y

    import x.y
    import x.y as z

    from x import y
    from x import y as z

    from x import y, z
    from a.b import c as d, e as f
"""
import logging
from pypyr.cache.namespacecache import pystring_namespace_cache

logger = logging.getLogger(__name__)


def run_step(context):
    """Import modules, classes or functions for PyString expressions.

    Args:
        context (pypyr.context.Context):
            Context is a dictionary or dictionary-like.
            Context must contain key 'pyImport'
            The value of pyImport is a string containing python import
            statements.
    """
    logger.debug("started")
    context.assert_key_has_value(key='pyImport', caller=__name__)

    # block yaml style could be LiteralScalarString, which is not hashable for
    # cache key. Explicitly make a string.
    source = str(context['pyImport'])

    namespace = pystring_namespace_cache.get_namespace(source)
    # len safe coz get_namespace returns {}, not None.
    logger.debug("imported %s objects to merge into PyString namespace",
                 len(namespace))

    new_length = context.pystring_globals_update(namespace)

    logger.debug("PyString namespace now contains %s objects.", new_length)

    logger.debug("done")
