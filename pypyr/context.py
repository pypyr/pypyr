"""pypyr context class. Dictionary ahoy."""


class Context(dict):
    """The pypyr context.

    This is a mutable dict that maintains state during the entire life-span of
    a pipeline.

    This class only adds functionality on top of dictionary, it should not
    override anything in dict.

    Attributes:
    """

    def assert_key_has_value(self, key, caller):
        """Assert that context contains key which also has a value.

        Args:
            key: validate this key exists in context
            caller: string. calling function name - this used to construct
                    error messages

        Raises:
            AssertionError: if dictionary is None, key doesn't exist in
                            dictionary, or dictionary[key] is None.

        """
        assert key, ("key parameter must be specified.")
        assert key in self, (
            f"context['{key}'] doesn't exist. It must have a value for "
            f"{caller}.")
        assert self[key], (
            f"context['{key}'] must have a value for {caller}.")

    def asserts_keys_have_values(self, keys, caller):
        """Check that keys list are all in context and all have values.

        Args:
            keys: list. Will check each of these keys in context
            caller: string. Calling function name - just used for informational
                    messages

        Raises:
            AssertionError: if dictionary is None, key doesn't exist in
                            dictionary, or dictionary[key] is None.
        """
        for key in keys:
            self.assert_key_has_value(key, caller)

    def get_formatted(self, key):
        """Returns formatted value for context[key].

        Only valid if context[key] is a type string.
        Return a string interpolated from the context dictionary.

        If context[key]='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        Args:
            key: dictionary key to retrieve.

        Returns:
            Formatted string.

        Raises:
            KeyError: context[key] value contains {somekey} where somekey does
                      not exist in context dictionary.
            TypeError: Attempt operation on a non-string type.
        """
        val = self[key]

        if isinstance(val, str):
            return val.format(**self)
        else:
            raise TypeError("can only format on strings. This is a "
                            "{type(val)} instead.")

    def get_formatted_string(self, input_string):
        """Returns formatted value for input_string.

        get_formatted gets a context[key] value.
        get_formatted_string is for any arbitrary string that is not in the
        context.

        Only valid if input_string is a type string.
        Return a string interpolated from the context dictionary.

        If input_string='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        Args:
            input_string: string to parse for substitutions.

        Returns:
            Formatted string.

        Raises:
            KeyError: context[key] has {somekey} where somekey does not exist
                      in context dictionary.
            TypeError: Attempt operation on a non-string type.
        """
        if isinstance(input_string, str):
            return input_string.format(**self)
        else:
            raise TypeError("can only format on strings. This is a "
                            "{type(val)} instead.")
