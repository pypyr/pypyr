"""pypyr context class. Dictionary ahoy."""
from collections import namedtuple

ContextItemInfo = namedtuple('ContextItemInfo',
                             ['key',
                              'key_in_context',
                              'expected_type',
                              'is_expected_type'])


class Context(dict):
    """The pypyr context.

    This is a mutable dict that maintains state during the entire life-span of
    a pipeline.

    This class only adds functionality on top of dictionary, it should not
    override anything in dict.
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

    def keys_exist(self, *keys):
        """Check if keys exist in context.

        Args:
            *keys: *args of str for keys to check in context.

        Returns:
            tuple (bool) where bool indicates the key does exist in context,
            same order as *keys.

        Sample:
            k1, = context.keys_exist('k1')
            k1, k2, k3 = context.keys_exist('k1', 'k2', 'k3')
        """
        return tuple(key in self.keys() for key in keys)

    def keys_of_type_exist(self, *keys):
        """Check if keys exist in context and if types are as expected.

        Args:
            *keys: *args for keys to check in context.
                   Each arg is a tuple (str, type)

        Returns:
            Tuple of namedtuple ContextItemInfo, same order as *keys.
            ContextItemInfo(key,
                            key_in_context,
                            expected_type,
                            is_expected_type)

            Remember if there is only one key in keys, the return assignment
            needs an extra comma to remind python that it's a tuple:
            # one
            a, = context.keys_of_type_exist('a')
            # > 1
            a, b = context.keys_of_type_exist('a', 'b')
        """
        # k[0] = key name, k[1] = exists, k2 = expected type
        keys_exist = [(key, key in self.keys(), expected_type)
                      for key, expected_type in keys]

        return tuple(ContextItemInfo(
            key=k[0],
            key_in_context=k[1],
            expected_type=k[2],
            is_expected_type=isinstance(self[k[0]], k[2])
            if k[1] else None
        ) for k in keys_exist)
