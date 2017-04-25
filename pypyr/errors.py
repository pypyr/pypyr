"""Custom exceptions for pypyr.

All pypyr specific exceptions derive from Error.
"""


class Error(Exception):
    """Base class for all pypyr exceptions."""


class PlugInError(Error):
    """Pypyr plug-ins should sub-class this."""
