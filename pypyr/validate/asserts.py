"""pypyr assertions to make life validating context easier."""


def key_in_context_has_value(context, key, caller):
    """Assert that validate_me contains key which has a value.

    Args:
        context: dictionary
        key: validate this key exists in context
        caller: calling function name - this used to construct error messages

    Raises:
        AssertionError: if dictionary is None, key doesn't exist in dictionary,
                        or dictionary[key] is None.

    """
    assert context, (f"context must be set for {caller}.")
    assert key, ("key parameter must be specified.")
    assert key in context, (
        f"context['{key}'] doesn't exist. It must have a value for "
        f"{caller}.")
    assert context[key], (
        f"context['{key}'] must have a value for {caller}.")
