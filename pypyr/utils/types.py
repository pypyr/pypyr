"""Utility functions for type checking, conversion and handling."""


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


def cast_to_type(obj, out_type):
    """Cast obj to out_type if it's not out_type already.

    If the obj happens to be out_type already, it just returns obj as is.

    Args:
        obj: input object
        out_type: type.

    Returns:
        obj cast to out_type. Usual python conversion / casting rules apply.

    """
    in_type = type(obj)
    if out_type is in_type:
        # no need to cast.
        return obj
    else:
        return out_type(obj)
