"""Guard utility functions for ensuring things exist or have values."""
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          KeyInContextHasNoValueError)


def assert_key_exists(obj, key, caller, parent=None):
    """Assert that object contains key.

    Error messages are structured as if obj is a pypyr Context.

    Args:
        obj (mapping): object to check for key.
        key (any valid key type): validates that this key exists in context
        caller: string. calling function or module name - this used to
                construct error messages. Tip: use .__name__
        parent (any valid key type): parent key name. Used to construct error
                                     messages to indicate the name of missing
                                     obj in context.

    Raises:
        KeyNotInContextError: When key doesn't exist in context.

    """
    try:
        if key not in obj:
            if parent:
                msg = (f"context[{parent!r}][{key!r}] doesn't "
                       f"exist. It must exist for {caller}.")
            else:
                msg = (
                    f"context[{key!r}] doesn't exist. "
                    f"It must exist for {caller}.")

            raise KeyNotInContextError(msg)
    except TypeError as err:
        # catches None on obj or obj not iterable
        if parent:
            msg = (f"context[{parent!r}] must exist, be iterable and contain "
                   f"{key!r} for {caller}. {err}")
        else:
            msg = (f"context[{key!r}] must exist and be iterable for "
                   f"{caller}. {err}")
        raise ContextError(msg) from err


def assert_key_has_value(obj, key, caller, parent=None):
    """Assert key exists in obj and has value.

    Does not eval on truthy. Empty string or 0 counts as a value.

    Error messages are structured as if obj is a pypyr Context.

    Args:
        obj (mapping): object to check for key.
        key (any valid key type): key to check in obj
        caller (string): calling function name - this used to construct
                         error messages. Tip: use .__name__
        parent (string): parent key name. Used to construct error messages to
                         indicate the name of obj in context.

    Raises:
        ContextError: if obj is None or not iterable.
        KeyInContextHasNoValueError: context[key] is None
        KeyNotInContextError: Key doesn't exist
    """
    assert_key_exists(obj, key, caller, parent)
    if obj[key] is None:
        if parent:
            msg = (f"context[{parent!r}][{key!r}] must have a value for "
                   f"{caller}.")
        else:
            msg = f"context[{key!r}] must have a value for {caller}."

        raise KeyInContextHasNoValueError(msg)


def assert_key_is_truthy(obj, key, caller, parent=None):
    """Assert key exists in obj and evaluates truthy.

    Empty string or 0 does NOT count as a value.

    Error messages are structured as if obj is a pypyr Context.

    Args:
        obj (mapping): object to check for key.
        key (any valid key type): key to check in obj
        caller (string): calling function name - this used to construct
                         error messages. Tip: use .__name__
        parent (string): parent key name. Used to construct error messages to
                         indicate the name of obj in context.

    Raises:
        ContextError: if obj is None or not iterable.
        KeyInContextHasNoValueError: if not bool(context[key])
        KeyNotInContextError: Key doesn't exist
    """
    assert_key_exists(obj, key, caller, parent)
    if not obj[key]:
        if parent:
            msg = (f"context[{parent!r}][{key!r}] must have a value for "
                   f"{caller}.")
        else:
            msg = f"context[{key!r}] must have a value for {caller}."

        raise KeyInContextHasNoValueError(msg)


def assert_keys_are_truthy(obj, keys, caller, parent=None):
    """Assert keys exists in obj and evaluates truthy.

    Empty string or 0 does NOT count as a value.

    Error messages are structured as if obj is a pypyr Context.

    Keys is an iterable of key names to check.

    Args:
        obj (mapping): object to check for key.
        keys (list[hashable]): iterable of keys to check in obj
        caller (string): calling function name - this used to construct
                         error messages. Tip: use .__name__
        parent (string): parent key name. Used to construct error messages to
                         indicate the name of obj in context.

    Raises:
        ContextError: if obj is None or not iterable.
        KeyInContextHasNoValueError: if not bool(context[key])
        KeyNotInContextError: Key doesn't exist
    """
    for key in keys:
        assert_key_is_truthy(obj, key, caller, parent)
