"""Custom exceptions for pypyr.

All pypyr specific exceptions derive from Error.
"""


def get_error_name(error):
    """Return canonical error name as string.

    For builtin errors like ValueError or Exception, will return the bare
    name, like ValueError or Exception.

    For all other exceptions, will return modulename.errorname, such as
    arbpackage.mod.myerror

    Args:
        error: Exception object.

    Returns:
        str. Canonical error name.

    """
    error_type = type(error)
    if error_type.__module__ in ['__main__', 'builtins']:
        return error_type.__name__
    else:
        return f'{error_type.__module__}.{error_type.__name__}'


class Error(Exception):
    """Base class for all pypyr exceptions."""


class ContextError(Error):
    """Error in the pypyr context."""


class KeyInContextHasNoValueError(ContextError):
    """pypyr context[key] doesn't have a value."""


class KeyNotInContextError(ContextError, KeyError):
    """Key not found in the pypyr context."""

    def __str__(self):
        """KeyError has custom error formatting, avoid this behaviour."""
        return super(Exception, self).__str__()


class LoopMaxExhaustedError(Error):
    """Max attempts reached during looping."""


class PipelineDefinitionError(Error):
    """Pipeline definition incorrect. Likely a yaml error."""


class PipelineNotFoundError(Error):
    """Pipeline not found in working dir or in pypyr install dir."""


class PlugInError(Error):
    """Pypyr plug-ins should sub-class this."""


class PyModuleNotFoundError(Error, ModuleNotFoundError):
    """Could not load python module because it wasn't found."""
