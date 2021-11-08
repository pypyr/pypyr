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


def cast_to_bool(obj):
    """Convert to bool with special string parsing.

    If obj is string: case-insensitive 'True', '1' or '1.0' is True.
    It will be False for all other strings.

    Any other object evaluates with standard truthy.

    Args:
        obj (any): Get truthy from this input object

    Returns:
        bool. Truthy value of input obj.
    """
    if isinstance(obj, str):
        return obj.lower() in ['true', '1', '1.0']
    else:
        return bool(obj)


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


def empty_if_none(obj):
    """Return empty string if obj is None.

    Args:
        obj (any): input object.

    Returns:
        obj if obj is truthy, else empty string.
    """
    return obj if obj else ''
