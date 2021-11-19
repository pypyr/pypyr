"""pypyr context class. Dictionary ahoy."""
from collections.abc import Mapping, Set
from collections import deque, namedtuple
from contextlib import contextmanager
import logging

from pypyr.dsl import SpecialTagDirective
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.formatting import RecursiveFormatter
from pypyr.moduleloader import _ChainMapPretendDict
from pypyr.utils import asserts, types

ContextItemInfo = namedtuple('ContextItemInfo',
                             ['key',
                              'key_in_context',
                              'expected_type',
                              'is_expected_type',
                              'has_value'])


logger = logging.getLogger(__name__)


class Context(dict):
    """The pypyr context.

    This is a mutable dict that maintains state during the entire life-span of
    a pipeline.

    This class only adds functionality on top of dictionary, it should not
    override anything in dict unless official Python docs mark a method as
    safe for override.

    Attributes:
        current_pipeline (pypyr.pipeline.Pipeline): instance of the currently
            running Pipeline. Don't set me directly, use context.pipeline_scope
            instead.
        is_in_pipeline_scope (bool): True if under active running pipeline
            scope.
    """

    # I *think* instantiating formatter at class level is fine - far as I can
    # see the class methods are functional, not dependant on class state (also,
    # no __init__).
    # https://github.com/python/cpython/blob/master/Lib/string.py
    formatter = RecursiveFormatter(special_types=SpecialTagDirective)

    # region dict overrides
    def __init__(self, *args, **kwargs):
        """Initialize context."""
        super().__init__(*args, **kwargs)
        # __builtins__ are in _ChainMapPretendDict, not in _pystring_globals
        self._pystring_globals = {}
        # working on assumption context more frequent lookup than builtins.
        # here context can go 1st, because eval expressions can't update the
        # namespace like exec does.
        self._pystring_namespace = _ChainMapPretendDict(self,
                                                        self._pystring_globals)

        # controlled via Context.pipeline_scope context manager.
        self._stack = deque()
        self.current_pipeline = None

    # region serialization
    def __getstate__(self):
        """Remove namespace from pickle serialization."""
        state = self.__dict__.copy()
        # no need to persist builtins - will rehydrate these on setstate.
        # do want to keep any custom py imports, though.
        del state['_pystring_namespace']

        # can't pickle Pipeline - refs PipelineDefinition in cache that might
        # not exist anymore
        del state['_stack']
        del state['current_pipeline']

        return state

    def __setstate__(self, state):
        """Rehydrate from pickle will fail on ChainMap coz invocation order.

        Thus custom override to set pystring globals 1st, then namespace with
        self ref.
        """
        self.__dict__.update(state)
        self._pystring_namespace = _ChainMapPretendDict(self,
                                                        self._pystring_globals)

        self._stack = deque()
        self.current_pipeline = None

    # endregion serialization

    def __missing__(self, key):
        """Throw KeyNotInContextError rather than KeyError.

        Python explicitly clears this over-ride for dict inheritance.
        https://docs.python.org/3/library/stdtypes.html#dict
        """
        raise KeyNotInContextError(f"{key} not found in the pypyr context.")

    # endregion dict overrides

    # region asserts

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
        asserts.assert_key_has_value(self,
                                     parent,
                                     caller)
        asserts.assert_key_has_value(self[parent],
                                     child,
                                     caller,
                                     parent)

    def assert_key_exists(self, key, caller):
        """Assert that context contains key.

        Args:
            key: validates that this key exists in context
            caller: string. calling function or module name - this used to
                    construct error messages

        Raises:
            KeyNotInContextError: When key doesn't exist in context.

        """
        asserts.assert_key_exists(self, key, caller)

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
        asserts.assert_key_has_value(self, key, caller)

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

    # endregion asserts

    # region formatting expressions
    def get_eval_string(self, input_string):
        """Dynamically evaluates the input_string python expression.

        This provides dynamic python eval of an input expression. The return is
        whatever the result of the expression is.

        Use with caution: since input_string executes any arbitrary code object
        the potential for damage is great.

        The eval unpacks the current context object into the namespace. This
        means if you have context['mykey'], in the input_string expression you
        can use the key directly as a variable like this:
        "mykey == 'mykeyvalue'".

        Both __builtins__ and context are available to the eval expression.

        Args: input_string: expression to evaluate.

        Returns: Whatever object results from the string expression valuation.

        """
        if input_string:
            return eval(input_string, self._pystring_namespace)
        else:
            # Empty input raises cryptic EOF syntax err, this more human
            # friendly
            raise ValueError('input expression is empty. It must be a valid '
                             'python expression instead.')

    def get_formatted(self, key):
        """Return formatted value for context[key].

        This is a convenience method that calls the same thing as
        get_formatted_value() under the hood, passing to it the value it
        retrieves from context at the input key.

        If context[key]'s value is a type string, will just format and return
        the string. Strings can contain recursive formatting expressions.

        If context[key]'s value is a special type, like a py string or sic
        string, will run the formatting implemented by the custom tag
        representer.

        If context[key] is not a string, specifically an iterable type like a
        dict, list, tuple, set, it will use get_formatted_value under the
        covers to loop through and handle the entire structure contained in
        context[key].

        If context[key]='Piping {key1} the {key2} wild'
        And context={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        Choosing between get_formatted() and get_formatted_value():
        - get_formatted() gets a context[key] value with formatting applied.
        - get_formatted_value() is for any arbitrary object.

        Args:
            key: dictionary key to retrieve.

        Returns:
            Whatever object results from the formatting expression(s) at the
            input key's value.

        Raises:
            KeyNotInContextError: context[key] value contains {somekey} where
                                  somekey does not exist in context dictionary.

        """
        val = self[key]

        try:
            # any sort of complex type will work with recursive formatter.
            return self.formatter.vformat(val, None, self)
        except KeyNotInContextError as err:
            # less cryptic error for end-user friendliness
            raise KeyNotInContextError(
                f'Unable to format \'{val}\' at context[\'{key}\'], '
                f'because {err}'
            ) from err

    def get_formatted_as_type(self, value, default=None, out_type=str):
        """Return formatted value for input value, returns as out_type.

        Caveat emptor: if out_type is bool and value a string,
        return will be True if str is 'True', 'TRUE', '1' or '1.0'. It will be
        False for all other cases.

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
            result = self.formatter.vformat(value, None, self)
            result_type = type(result)
            if out_type is result_type:
                # no need to cast, result is already desired type.
                return result
            elif out_type is bool:
                # casting a str to bool is always True, hence special case. If
                # the str value is 'False'/'false', presumably user can
                # reasonably expect a bool False response.
                return types.cast_to_bool(result)
            else:
                return out_type(result)
        else:
            return out_type(value)

    def get_formatted_value(self, input_value):
        """Run token substitution on the input against context.

        If input_value is a formattable string or SpecialTagDirective,
        will return the formatted result.

        If input_value is an iterable, will iterate input recursively and
        format all formattable objects it finds. Mappings will format both key
        and value.

        If input_value is not a string with a formatting expression such as
        'mystring{expr}morestring' and not iterable, will just return the input
        object. E.g An int input will return the same int.

        Choosing between get_formatted() and get_formatted_value():
        - get_formatted gets a context[key] value with formatting applied.
        - get_formatted_value is for any input object.

        An input string with a single formatting expression and nothing else
        will return the object at that context path:
        input_value = '{key1}'.

        This means that the return obj will be the same type as the source
        object. This return object in itself has token substitions run on it
        iteratively.

        By comparison, multiple formatting expressions and/or the inclusion
        of literal text will result in a string return type:
        input_value = '{key1} literal text {key2}'

        Then this will return string: "Piping down the valleys wild"

        This is not a full on deepcopy, and it's on purpose not a full on
        deepcopy. It will handle dict, list, set, tuple for iteration, without
        any especial cuteness for other types or types not derived from these.

        Returns:
            Iterable identical in structure to the input iterable, except
            where formatting changed a value from a string to the
            formatting expression's evaluated value.

        Args:
            input_value: Any object to format.

        Returns:
            any given type: Formatted value with {substitutions} made from
            context. If input was not a string, will just return input_value
            untouched.

        """
        return self.formatter.vformat(input_value, None, self)

    def iter_formatted_strings(self, iterable_strings):
        """Yield a formatted string from iterable_strings.

        If iterable_strings[0] = 'Piping {key1} the {key2} wild'
        And context = {'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then the 1st yield is: "Piping down the valleys wild"

        Args:
            iterable: Iterable containing strings. E.g a file-like object.

        Returns:
            Yields formatted line.

        """
        for string in iterable_strings:
            yield self.formatter.vformat(string, None, self)

    # endregion formatting expressions

    def keys_exist(self, *keys):
        """Check if keys exist in context.

        Args:
            *keys: *args of str for keys to check in context.

        Returns:
            tuple(bool) where bool indicates the key does exist in context,
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
                   Each arg is a tuple(str, type)

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

            On 1st iteration, current = self(i.e root of context)
            On subsequent recursive iterations, current is wherever you're at
            in the nested context hierarchy.

            Args:
                current: dict. Destination of merge.
                add_me: dict. Merge this to current.
            """
            for k, v in add_me.items():
                # key supports interpolation
                k = self.get_formatted_value(k)

                # str not mergable, so it doesn't matter if it exists in dest
                if isinstance(v, (str, SpecialTagDirective)):
                    # just overwrite dest - str adds/edits indiscriminately
                    current[k] = self.get_formatted_value(v)
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
                            self.get_formatted_value(v))
                    elif types.are_all_this_type(tuple, current[k], v):
                        # concatenate tuples
                        current[k] = (
                            current[k] + self.get_formatted_value(v))
                    elif types.are_all_this_type(Set, current[k], v):
                        # join sets
                        current[k] = (
                            current[k] | self.get_formatted_value(v))
                    else:
                        # at this point it's not mergable
                        current[k] = self.get_formatted_value(v)
                else:
                    # at this point it's not mergable, nor in context
                    current[k] = self.get_formatted_value(v)

        # first iteration starts at context dict root
        merge_recurse(self, add_me)

    # region pipeline_scope

    @contextmanager
    def pipeline_scope(self, pipeline):
        """Set the currently active pipeline on this context instance.

        pypyr keeps track of the pipeline call-chain with a stack. This is
        relevant when parent pipelines call child pipelines using
        pypyr.steps.pype.

        This scope adds the current pipeline's Pipeline instance to the stack
        when it starts running.

        When the pipeline finishes, removes it from the stack.

        This is a context manager, so use with "with" for an easy life.

        Args:
            pipeline (pypyr.pipeline.Pipeline): Add this Pipeline object to the
                stack.
        """
        pipeline_name = pipeline.name
        stack = self._stack
        try:
            logger.debug('entering pipeline scope: %s', pipeline_name)
            stack.append(pipeline)
            self.current_pipeline = pipeline
            yield
        finally:
            logger.debug('exiting pipeline scope: %s', pipeline_name)
            stack.pop()
            self.current_pipeline = stack[-1] if stack else None

    def get_root_pipeline(self):
        """Get the Pipeline instance of the root pipeline.

        The root pipeline is the very first pipeline in the call stack.
        """
        try:
            # This is O(1).
            return self._stack[0]
        except IndexError as err:
            raise ContextError(
                "There is no pipeline scope set on this context instance. A "
                "pipeline should run inside a pipeline_scope for this method "
                "to return the root pipeline.") from err

    def get_stack_depth(self):
        """Get how many pipelines are in the current call stack."""
        return len(self._stack)

    @property
    def is_in_pipeline_scope(self):
        """Return True if context under active pipeline_scope."""
        return bool(self._stack)

    # endregion pipeline_scope

    # region pystring global namespace
    def pystring_globals_clear(self):
        """Clear the pystring globals namespace."""
        self._pystring_globals.clear()

    def pystring_globals_update(self, *args, **kwargs):
        """Update the pystring globals namespace with values from other.

        Args:
            *args/**kwargs:
                - iterable of key/value pairs
                - dict

        Returns:
            Length of updated pystring globals.
        """
        # pystring_globals initialized to {} on Context init, no None worries.
        self._pystring_globals.update(*args, **kwargs)
        return len(self._pystring_globals)

    # region pystring global namespace

    def set_defaults(self, defaults):
        """Set defaults in context if keys do not exist already.

        Adds the input dict(defaults) into the context, only where keys in
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

            On 1st iteration, current = self(i.e root of context)
            On subsequent recursive iterations, current is wherever you're at
            in the nested context hierarchy.

            Args:
                current: dict. Destination of merge.
                defaults: dict. Add this to current if keys don't exist
                                already.

            """
            for k, v in defaults.items():
                # key supports interpolation
                k = self.get_formatted_value(k)

                if k in current:
                    if types.are_all_this_type(Mapping, current[k], v):
                        # it's dict-y, thus recurse through it to check if it
                        # contains child items that don't exist in dest
                        defaults_recurse(current[k], v)
                else:
                    # since it's not in context already, add the default
                    current[k] = self.get_formatted_value(v)

        # first iteration starts at context dict root
        defaults_recurse(self, defaults)
