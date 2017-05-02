"""Custom exceptions for pypyr.

All pypyr specific exceptions derive from Error.
"""


class Error(Exception):
    """Base class for all pypyr exceptions."""


class ContextError(Error):
    """Error in the pypyr context."""


class KeyInContextHasNoValueError(ContextError):
    """pypyr context[key] doesn't have a value."""


class KeyNotInContextError(ContextError):
    """Key not found in the pypyr context."""


class PipelineNotFoundError(Error):
    """Pipeline not found in working dir or in pypyr install dir."""


class PlugInError(Error):
    """Pypyr plug-ins should sub-class this."""


class PyModuleNotFoundError(Error):
    """Could not load python module because it wasn't found."""
