"""pypyr string formatting."""


def get_interpolated_string(input_string, context):
    """Return a string interpolated from the context dictionary.

    If input_string='Piping {key1} the {key2} wild'
    And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

    Then this will return string: "Piping down the valleys wild"

    Args:
        input_string: string literal to evaluate.
        context: dictionary. will interpolate input_string based on finding
                 keys in curly braces {} in input_string.

    Returns:
        string

    Raises:
        KeyError: if input_string has {key} where key does not exist in
                  context dictionary.
    """
    return input_string.format(**context)
