"""pypyr context class. Dictionary ahoy."""
from collections import namedtuple
from collections.abc import Mapping, Set, Sequence
from string import Formatter
from pypyr.dsl import SpecialTagDirective
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.utils import expressions, types

ContextItemInfo = namedtuple('ContextItemInfo',
                             ['key',
                              'key_in_context',
                              'expected_type',
                              'is_expected_type',
                              'has_value'])

# I *think* instantiating formatter at module level is fine - far as I can see
# the class methods are functional, not dependant on class state (also, no
# __init__).
# https://github.com/python/cpython/blob/master/Lib/string.py
formatter = Formatter()


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

    def assert_child_key_has_value(self, parent, child, caller):
        """Assert that context contains key that has child which has a value.

        Args:
            parent: parent key
            child: validate this sub-key of parent exists AND isn't None.
            caller: string. calling function name - this used to construct
                    error messages

        Raises:
            KeyNotInContextError: Key doesn't exist
            KeyInContextHasNoValueError: context[key] is None
            AssertionError: if key is None

        """
        assert parent, ("parent parameter must be specified.")
        assert child, ("child parameter must be specified.")
        self.assert_key_has_value(parent, caller)

        try:
            child_exists = child in self[parent]
        except TypeError as err:
            # This happens if parent isn't iterable
            raise ContextError(
                f"context['{parent}'] must be iterable and contain '{child}' "
                f"for {caller}. {err}") from err

        if child_exists:
            if self[parent][child] is None:
                raise KeyInContextHasNoValueError(
                    f"context['{parent}']['{child}'] must have a value for "
                    f"{caller}.")
        else:
            raise KeyNotInContextError(
                f"context['{parent}']['{child}'] doesn't "
                f"exist. It must exist for {caller}.")

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

    def get_eval_string(self, input_string):
        """Dynamically evaluates the input_string expression.

        This provides dynamic python eval of an input expression. The return is
        whatever the result of the expression is.

        Use with caution: since input_string executes any arbitrary code object
        the potential for damage is great.

        The eval uses the current context object as the namespace. This means
        if you have context['mykey'], in the input_string expression you can
        use the key directly as a variable like this: "mykey == 'mykeyvalue'".

        Both __builtins__ and context are available to the eval expression.

        Args:
            input_string: expression to evaluate.

        Returns:
            Whatever object results from the string expression valuation.

        """
        return expressions.eval_string(input_string, dict(self))

    def get_formatted(self, key):
        """Return formatted value for context[key].

        If context[key] is a type string, will just format and return the
        string.
        If context[key] is a special literal type, like a py string or sic
        string, will run the formatting implemented by the custom tag
        representer.
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
            except KeyNotInContextError as err:
                # Wrapping the KeyError into a less cryptic error for end-user
                # friendliness
                raise KeyNotInContextError(
                    f'Unable to format \'{val}\' at context[\'{key}\'], '
                    f'because {err}'
                ) from err
        elif isinstance(val, SpecialTagDirective):
            return val.get_value(self)
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
        elif isinstance(obj, SpecialTagDirective):
            new = obj.get_value(self)
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
        """Return formatted value for input_string.

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
            KeyNotInContextError: context[key] has {somekey} where somekey does
                                  not exist in context dictionary.
            TypeError: Attempt operation on a non-string type.

        """
        if isinstance(input_string, str):
            try:
                return self.get_processed_string(input_string)
            except KeyNotInContextError as err:
                # Wrapping the KeyError into a less cryptic error for end-user
                # friendliness
                raise KeyNotInContextError(
                    f'Unable to format \'{input_string}\' because {err}'
                ) from err
        elif isinstance(input_string, SpecialTagDirective):
            return input_string.get_value(self)
        else:
            raise TypeError(f"can only format on strings. {input_string} is a "
                            f"{type(input_string)} instead.")

    def get_formatted_as_type(self, value, default=None, out_type=str):
        """Return formatted value for input value, returns as out_type.

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

        if isinstance(value, SpecialTagDirective):
            result = value.get_value(self)
            return types.cast_to_type(result, out_type)
        if isinstance(value, str):
            result = self.get_formatted_string(value)
            result_type = type(result)
            if out_type is result_type:
                # get_formatted_string result is already a string
                return result
            elif out_type is bool and result_type is str:
                # casting a str to bool is always True, hence special case. If
                # the str value is 'False'/'false', presumably user can
                # reasonably expect a bool False response.
                return result.lower() in ['true', '1', '1.0']
            else:
                return out_type(result)
        else:
            return out_type(value)

    def get_processed_string(self, input_string):
        """Run token substitution on input_string against context.

        You probably don't want to call this directly yourself - rather use
        get_formatted, get_formatted_iterable, or get_formatted_string because
        these contain more friendly error handling plumbing and context logic.

        If you do want to call it yourself, go for it, it doesn't touch state.

        If input_string='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        An input string with a single formatting expression and nothing else
        will return the object at that context path: input_string='{key1}'.
        This means that the return obj will be the same type as the source
        object. This return object in itself has token substitions run on it
        iteratively.

        By comparison, multiple formatting expressions and/or the inclusion of
        literal text will result in a string return type:
        input_string='{key1} literal text {key2}'

        Then this will return string: "Piping down the valleys wild"

        Args:
            input_string: string to Parse

        Returns:
            any given type: Formatted string with {substitutions} made from
            context. If it's a !sic string, x from !sic x, with no
            substitutions made on x. If input_string was a single expression
            (e.g '{field}'), then returns the object with {substitutions} made
            for its attributes.

        Raises:
            KeyNotInContextError: input_string is not a sic string and has
                                  {somekey} where somekey does not exist in
                                  context dictionary.

        """
        # arguably, this doesn't really belong here, or at least it makes a
        # nonsense of the function name. given how py and strings
        # look and feel pretty much like strings from user's perspective, and
        # given legacy code back when sic strings were in fact just strings,
        # keep in here for backwards compatibility.
        if isinstance(input_string, SpecialTagDirective):
            return input_string.get_value(self)
        else:
            # is this a special one field formatstring? i.e "{field}", with
            # nothing else?
            out = None
            is_out_set = False
            expr_count = 0
            # parse finds field format expressions and/or literals in input
            for expression in formatter.parse(input_string):
                # parse tuple:
                # (literal_text, field_name, format_spec, conversion)
                # it's a single '{field}' if no literal_text but field_name
                # no literal, field name exists, and no previous expr found
                if (not expression[0] and expression[1] and not expr_count):
                    # get_field tuple: (obj, used_key)
                    out = formatter.get_field(expression[1], None, self)[0]
                    # second flag necessary because a literal with no format
                    # expression will still result in expr_count == 1
                    is_out_set = True

                expr_count += 1

                # this is a little bit clumsy, but you have to consume the
                # iterator to get the count. Interested in 1 and only 1 field
                # expressions with no literal text: have to loop to see if
                # there is >1.
                if expr_count > 1:
                    break

            if is_out_set and expr_count == 1:
                # found 1 and only 1. but this could be an iterable obj
                # that needs formatting rules run on it in itself
                return self.get_formatted_iterable(out)
            else:
                return input_string.format_map(self)

    def iter_formatted_strings(self, iterable_strings):
        """Yield a formatted string from iterable_strings.

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

    def merge(self, add_me):
        """Merge add_me into context and applies interpolation.

        Bottom-up merge where add_me merges into context. Applies string
        interpolation where the type is a string. Where a key exists in
        context already, add_me's value will overwrite what's in context
        already.

        Supports nested hierarchy. add_me can contains dicts/lists/enumerables
        that contain other enumerables et. It doesn't restrict levels of
        nesting, so if you really want to go crazy with the levels you can, but
        you might blow your stack.

        If something from add_me exists in context already, but add_me's value
        is of a different type, add_me will overwrite context. Do note this.
        i.e if you had context['int_key'] == 1 and
        add_me['int_key'] == 'clearly not a number', the end result would be
        context['int_key'] == 'clearly not a number'

        If add_me contains lists/sets/tuples, this merges these
        additively, meaning it appends values from add_me to the existing
        sequence.

        Args:
            add_me: dict. Merge this dict into context.

        Returns:
            None. All operations mutate this instance of context.

        """
        def merge_recurse(current, add_me):
            """Walk the current context tree in recursive inner function.

            On 1st iteration, current = self (i.e root of context)
            On subsequent recursive iterations, current is wherever you're at
            in the nested context hierarchy.

            Args:
                current: dict. Destination of merge.
                add_me: dict. Merge this to current.
            """
            for k, v in add_me.items():
                # key supports interpolation
                k = self.get_formatted_string(k)

                # str not mergable, so it doesn't matter if it exists in dest
                if isinstance(v, str):
                    # just overwrite dest - str adds/edits indiscriminately
                    current[k] = self.get_formatted_string(v)
                elif isinstance(v, (bytes, bytearray)):
                    # bytes aren't mergable or formattable
                    # only here to prevent the elif on enumerables catching it
                    current[k] = v
                # deal with things that are mergable - exists already in dest
                elif k in current:
                    if types.are_all_this_type(Mapping, current[k], v):
                        # it's dict-y, thus recurse through it to merge since
                        # it exists in dest
                        merge_recurse(current[k], v)
                    elif types.are_all_this_type(list, current[k], v):
                        # it's list-y. Extend mutates existing list since it
                        # exists in dest
                        current[k].extend(
                            self.get_formatted_iterable(v))
                    elif types.are_all_this_type(tuple, current[k], v):
                        # concatenate tuples
                        current[k] = (
                            current[k] + self.get_formatted_iterable(v))
                    elif types.are_all_this_type(Set, current[k], v):
                        # join sets
                        current[k] = (
                            current[k] | self.get_formatted_iterable(v))
                    else:
                        # at this point it's not mergable nor a known iterable
                        current[k] = v
                else:
                    # at this point it's not mergable, nor in context
                    current[k] = self.get_formatted_iterable(v)

        # first iteration starts at context dict root
        merge_recurse(self, add_me)

    def set_defaults(self, defaults):
        """Set defaults in context if keys do not exist already.

        Adds the input dict (defaults) into the context, only where keys in
        defaults do not already exist in context. Supports nested hierarchies.

        Example:
        Given a context like this:
            key1: value1
            key2:
                key2.1: value2.1
            key3: None

        And defaults input like this:
            key1: 'updated value here won't overwrite since it already exists'
            key2:
                key2.2: value2.2
            key3: 'key 3 exists so I won't overwrite

        Will result in context:
            key1: value1
            key2:
                key2.1: value2.1
                key2.2: value2.2
            key3: None

        Args:
            defaults: dict. Add this dict into context.

        Returns:
            None. All operations mutate this instance of context.

        """
        def defaults_recurse(current, defaults):
            """Walk the current context tree in recursive inner function.

            On 1st iteration, current = self (i.e root of context)
            On subsequent recursive iterations, current is wherever you're at
            in the nested context hierarchy.

            Args:
                current: dict. Destination of merge.
                defaults: dict. Add this to current if keys don't exist
                                already.

            """
            for k, v in defaults.items():
                # key supports interpolation
                k = self.get_formatted_string(k)

                if k in current:
                    if types.are_all_this_type(Mapping, current[k], v):
                        # it's dict-y, thus recurse through it to check if it
                        # contains child items that don't exist in dest
                        defaults_recurse(current[k], v)
                else:
                    # since it's not in context already, add the default
                    current[k] = self.get_formatted_iterable(v)

        # first iteration starts at context dict root
        defaults_recurse(self, defaults)
