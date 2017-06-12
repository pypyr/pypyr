"""pypyr context class. Dictionary ahoy."""
from collections import namedtuple
from collections.abc import Mapping, Set, Sequence
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

    Attributes:
        working_dir (path-like): working directory path. Either CWD or
                                 initialized from the cli --dir arg.
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

        If context[key] is a type string, will just format and return the
        string.
        If context[key] is not a string, specifically an iterable type like a
        dict, list, tuple, set, it will use get_formatted_iterable under the
        covers to loop through and handle the entire structure contained in
        context[key].

        Returns a string interpolated from the context dictionary.

        If context[key]='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        Args:
            key: dictionary key to retrieve.

        Returns:
            Formatted string.

        Raises:
            KeyNotInContextError: context[key] value contains {somekey} where
                                  somekey does not exist in context dictionary.
        """
        val = self[key]

        if isinstance(val, str):
            try:
                return self.get_processed_string(val)
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
            # any sort of complex type will work with get_formatted_iterable.
            return self.get_formatted_iterable(val)

    def get_formatted_iterable(self, obj, memo=None):
        """Recursively loop through obj, formatting as it goes.

        Interpolates strings from the context dictionary.

        This is not a full on deepcopy, and it's on purpose not a full on
        deepcopy. It will handle dict, list, set, tuple for iteration, without
        any especial cuteness for other types or types not derived from these.

        For lists: if value is a string, format it.
        For dicts: format key. If value str, format it.
        For sets/tuples: if type str, format it.

        This is what formatting or interpolating a string means:
        So where a string like this 'Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        Args:
            obj: iterable. Recurse through and format strings found in
                           dicts, lists, tuples. Does not mutate the input
                           iterable.
            memo: dict. Don't use. Used internally on recursion to optimize
                        recursive loops.

        Returns:
            Iterable identical in structure to the input iterable.
        """

        if memo is None:
            memo = {}

        obj_id = id(obj)
        already_done = memo.get(obj_id, None)
        if already_done is not None:
            return already_done

        if isinstance(obj, str):
            new = self.get_formatted_string(obj)
        elif isinstance(obj, (bytes, bytearray)):
            new = obj
        elif isinstance(obj, Mapping):
            # dicts
            new = obj.__class__()
            for k, v in obj.items():
                new[self.get_formatted_string(
                    k)] = self.get_formatted_iterable(v, memo)
        elif isinstance(obj, (Sequence, Set)):
            # list, set, tuple. Bytes and str won't fall into this branch coz
            # they're expicitly checked further up in the if.
            new = obj.__class__(self.get_formatted_iterable(v, memo)
                                for v in obj)
        else:
            # int, float, bool, function, et.
            return obj

        # If is its own copy, don't memoize.
        if new is not obj:
            memo[obj_id] = new

        return new

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
                return self.get_processed_string(input_string)
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

    def get_formatted_as_type(self, value, default=None, out_type=str):
        """Returns formatted value for input value, returns as out_type.

        Caveat emptor: if out_type is bool and value a string,
        return will be True if str is 'True'. It will be False for all other
        cases.

        Args:
            value: the value to format
            default: if value is None, set to this
            out_type: cast return as this type

        Returns:
            Formatted value of type out_type
        """
        if value is None:
            value = default

        if isinstance(value, str):
            result = self.get_formatted_string(value)

            if out_type is str:
                # get_formatted_string result is already a string
                return result
            elif out_type is bool:
                # casting a str to bool is always True, hence special case. If
                # the str value is 'False'/'false', presumably user can
                # reasonably expect a bool False response.
                return result == 'True'
            else:
                return out_type(result)
        else:
            return value

    def get_processed_string(self, input_string):
        """Runs token substitution on input_string against context.

        You probably don't want to call this directly yourself - rather use
        get_formatted, get_formatted_iterable, or get_formatted_string because
        these contain more friendly error handling plumbing and context logic.

        If you do want to call it yourself, go for it, it doesn't touch state.

        If input_string='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        If a string is NOT to have {substitutions} run on it, it's sic erat
        scriptum, i.e literal.

        A sic string looks like this:
        input_string=[sic]"<<your string literal here>>"

        For example:
            [sic]"piping {key} the valleys wild"

        Will return "piping {key} the valleys wild" without attempting to
        substitute {key} from context.

        Args:
            input_string: string to Parse

        Returns:
            str: Formatted string with {substitutions} made from context. If
            it's a [sic] string, x from [sic]"x", with no substitutions made on
            x.

        Raises:
            KeyError: input_string is not a sic string and has {somekey} where
                      somekey does not exist in context dictionary.
        """
        if input_string[:6] == '[sic]"':
            return input_string[6: -1]
        else:
            return input_string.format(**self)

    def iter_formatted_strings(self, iterable_strings):
        """Generator that yields a formatted string from iterable_strings

        If iterable_strings[0]='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then the 1st yield is: "Piping down the valleys wild"

        Args:
            iterable: Iterable containing strings. E.g a file-like object.

        Returns:
            Yields formatted line.
        """
        for string in iterable_strings:
            yield self.get_formatted_string(string)

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
