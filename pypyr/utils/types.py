""""Utility functions for type checking, conversion and handling."""
import logging

# pypyr logger means the log level will be set correctly and output formatted.
logger = logging.getLogger(__name__)


def are_all_this_type(type, *objects):
    """Return True if all objects are instances of this type.

    Args:
        type: Type to check against, e.g str, dict
        objects: *args of objects. Each of these will be checked against type.

    Returns:
        True is all objects are instances of specified Type.
        False if any or all of the objects are not instances of Type.
    """
    # return true if all objects are instances of type
    return all(isinstance(object, type) for object in objects)
