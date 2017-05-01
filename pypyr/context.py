"""pypyr context class. Dictionary ahoy."""
from collections import namedtuple
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError

ContextItemInfo = namedtuple('ContextItemInfo',
                             ['key',
                              'key_in_context',
                              'expected_type',
                              'is_expected_type',
                              'has_value'])


class Context(dict):
    """The pypyr context.

    This is a mutable dict that maintains state during the entire life-span of
    a pipeline.

    This class only adds functionality on top of dictionary, it should not
    override anything in dict.
    """

    def __missing__(self, key):
        """Throw KeyNotInContextError rather than KeyError.

        Python explicitly clears this over-ride for dict inheritance.
        https://docs.python.org/3/library/stdtypes.html#dict
        """
        raise KeyNotInContextError(f"{key} not found in the pypyr context.")

    def assert_key_exists(self, key, caller):
        """Assert that context contains key.

        Args:
            key: validates that this key exists in context
            caller: string. calling function or module name - this used to
                    construct error messages

        Raises:
            KeyNotInContextError: When key doesn't exist in context.
        """
        assert key, ("key parameter must be specified.")
        if key not in self:
            raise KeyNotInContextError(
                f"context['{key}'] doesn't exist. It must exist for {caller}.")

    def assert_key_has_value(self, key, caller):
        """Assert that context contains key which also has a value.

        Args:
            key: validate this key exists in context AND has a value that isn't
                 None.
            caller: string. calling function name - this used to construct
                    error messages

        Raises:
            KeyNotInContextError: Key doesn't exist
            KeyInContextHasNoValueError: context[key] is None
            AssertionError: if key is None

        """
        assert key, ("key parameter must be specified.")
        self.assert_key_exists(key, caller)

        if self[key] is None:
            raise KeyInContextHasNoValueError(
                f"context['{key}'] must have a value for {caller}.")

    def assert_key_type_value(self,
                              context_item,
                              caller,
                              extra_error_text=''):
        """Assert that keys exist of right type and has a value.

        Args:
             context_item: ContextItemInfo tuple
             caller: string. calling function name - this used to construct
                     error messages
             extra_error_text: append to end of error message.

        Raises:
            AssertionError: if context_item None.
            KeyNotInContextError: Key doesn't exist
            KeyInContextHasNoValueError: context[key] is None or the wrong
                                         type.
         """
        assert context_item, ("context_item parameter must be specified.")

        if extra_error_text is None or extra_error_text == '':
            append_error_text = ''
        else:
            append_error_text = f' {extra_error_text}'

        if not context_item.key_in_context:
            raise KeyNotInContextError(f'{caller} couldn\'t find '
                                       f'{context_item.key} in context.'
                                       f'{append_error_text}')

        if not context_item.has_value:
            raise KeyInContextHasNoValueError(
                f'{caller} found {context_item.key} in '
                f'context but it doesn\'t have a value.'
                f'{append_error_text}')

        if not context_item.is_expected_type:
            raise KeyInContextHasNoValueError(
                f'{caller} found {context_item.key} in context, but it\'s '
                f'not a {context_item.expected_type}.'
                f'{append_error_text}')

    def assert_keys_exist(self, caller, *keys):
        """Assert that context contains keys.

        Args:
            keys: validates that these keys exists in context
            caller: string. calling function or module name - this used to
                    construct error messages

        Raises:
            KeyNotInContextError: When key doesn't exist in context.
        """
        assert keys, ("*keys parameter must be specified.")
        for key in keys:
            self.assert_key_exists(key, caller)

    def assert_keys_have_values(self, caller, *keys):
        """Check that keys list are all in context and all have values.

        Args:
            *keys: Will check each of these keys in context
            caller: string. Calling function name - just used for informational
                    messages

        Raises:
            KeyNotInContextError: Key doesn't exist
            KeyInContextHasNoValueError: context[key] is None
            AssertionError: if *keys is None
        """
        for key in keys:
            self.assert_key_has_value(key, caller)

    def assert_keys_type_value(self,
                               caller,
                               extra_error_text,
                               *context_items):
        """Assert that keys exist of right type and has a value.

        Args:
             caller: string. calling function name - this used to construct
                     error messages
             extra_error_text: append to end of error message. This can happily
                               be None or ''.
            *context_items: ContextItemInfo tuples

        Raises:
            AssertionError: if context_items None.
            KeyNotInContextError: Key doesn't exist
            KeyInContextHasNoValueError: context[key] is None or the wrong
                                         type.
        """
        assert context_items, ("context_items parameter must be specified.")

        for context_item in context_items:
            self.assert_key_type_value(context_item, caller, extra_error_text)

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
            try:
                return val.format(**self)
            except KeyError as err:
                # Wrapping the KeyError into a less cryptic error for end-user
                # friendliness
                missing_key = err.args[0]
                raise KeyNotInContextError(
                    f'Unable to format \'{val}\' at context[\'{key}\'] with '
                    f'{{{missing_key}}}, because '
                    f'context[\'{missing_key}\'] doesn\'t exist'
                ) from err
        else:
            raise TypeError(f"can only format on strings. {val} is a "
                            f"{type(val)} instead.")

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
            try:
                return input_string.format(**self)
            except KeyError as err:
                # Wrapping the KeyError into a less cryptic error for end-user
                # friendliness
                missing_key = err.args[0]
                raise KeyNotInContextError(
                    f'Unable to format \'{input_string}\' with '
                    f'{{{missing_key}}}, because '
                    f'context[\'{missing_key}\'] doesn\'t exist') from err
        else:
            raise TypeError(f"can only format on strings. {input_string} is a "
                            f"{type(input_string)} instead.")

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
            if k[1] else None,
            has_value=k[1] and not self[k[0]] is None
        ) for k in keys_exist)
