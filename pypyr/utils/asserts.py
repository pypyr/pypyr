"""Guard utility functions for ensuring things exist or have values."""
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          KeyInContextHasNoValueError)


def assert_key_has_value(obj, key, caller, parent=None):
    """Assert key exists in obj and has value.

    Does not eval on truthy. Empty string or 0 counts as a value.

    Args:
        obj (mapping): object to check for key.
        key (string): key to check in obj
        caller (string): calling function name - this used to construct
                         error messages. Tip: use .__name__
        parent (string): parent key name. Used to construct error messages to
                         indicate the name of obj in context.

    Raises:
        ContextError: if obj is None.
        KeyInContextHasNoValueError: context[key] is None
        KeyNotInContextError: Key doesn't exist
    """
    if not obj:
        if parent:
            msg = (f"context['{parent}'] must exist and contain "
                   f"'{key}' for {caller}.")
        else:
            msg = (f"context['{key}'] must exist for {caller}.")
        raise ContextError(msg)

    if key not in obj:
        if parent:
            msg = (f"context['{parent}']['{key}'] doesn't "
                   f"exist. It must exist for {caller}.")
        else:
            msg = (f"context['{key}'] doesn't exist. It must exist for "
                   f"{caller}.")
        raise KeyNotInContextError(msg)
    else:
        if obj[key] is None:
            if parent:
                msg = (f"context['{parent}']['{key}'] must have a value for "
                       f"{caller}.")
            else:
                msg = f"context['{key}'] must have a value for {caller}."

            raise KeyInContextHasNoValueError(msg)
