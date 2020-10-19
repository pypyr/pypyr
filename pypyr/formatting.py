"""Substitution & interpolation formatting."""
from collections.abc import Mapping, Set, Sequence
from string import Formatter


class RecursionSpec():
    """Parse a string formatting spec.

    This class just parses a format_spec string. It looks for a leading 'ff' or
    'rf'.

    A format expression looks like this: {field_name!conversion:format_spec}

    The format_spec is everything after the ':'.

    It makes no attempt to implement business logic around what to do with the
    formatting string.

    Attributes:
        format_spec: The original format_spec without the leading 'ff' or 'rf'.
                     If is_set is False, is identical to input format_spec.
        has_recursed (bool): True if recursive operation completed for this
                             expression.
        is_flat (bool): True if format_spec starts with 'ff'.
        is_set (bool): True if format_spec is either 'ff' or 'rf'.
        is_recursive (bool): True if format_spec starts with 'rf'.
    """

    def __init__(self, format_spec):
        """Parse format_spec for recursion specifier.

        Args:
            format_spec (str): format specification parsed from string
                               formatting expression. Likely from Formatter's
                               .parse method.
        """
        recursion_spec = format_spec[:2]
        self.has_recursed = False
        self.is_set = False
        self.is_recursive = False
        self.is_flat = False

        if recursion_spec == 'rf':
            self.is_set = self.is_recursive = True
        elif recursion_spec == 'ff':
            self.is_set = self.is_flat = True

        self.format_spec = format_spec[2:] if self.is_set else format_spec


class RecursiveFormatter(Formatter):
    """Recursive or flat string formatting using standard python syntax.

    This maintains all the functionality of the standard python Formatter, only
    adding additional recursion to deal with nested formatting expressions. You
    can use conversions and format_spec as per usual. You can derive your own
    class and implement the standard overloads like get_field() and get_value()
    yourself.

    Full documentation here:
    https://docs.python.org/3/library/string.html#format-string-syntax

    A format expression looks like this: {field_name!conversion:format_spec}

    Both conversion and format_spec are optional.

    Recursive format means that if field_name resolves to a string that
    contains another formatting expression (a string with {} in it), it will
    keep formatting the result recursively until the result is a literal or
    object without any formatting expressions.

    Differs from the standard Python string.Formatter class in these ways:
    - If the input is an iterable object, iterates it recursively & applies
      formatting on all string types it finds in it.
    - Starting a format_spec with 'ff' formats once. (This is the default
      python string.Formatter behavior also).
    - Starting a format_spec with 'rf' formats recursively, until it
      encounters a `ff`.
    - Where a string has no format_spec, and contains a combination of
      literal and expression values, do standard flat format. For example,
      'arb {key} more arb' will format key once and cast the resulting value to
      string.
    - Where a string has no format_spec, and contains one and only one
      expression and nothing else, format recursively and keep the type of the
      source object. So where a formatting expression is '{key}', format
      recursively and return the ultimate value that key resolves to without
      casting it to string.

    You can still use all the usual format_spec functionality by adding the
    specifiers immediately after the 'ff' or 'rf'.

    Attributes:
        passthrough_types (tuple of type): Objects of this type do not format
                                           at all - pass through without
                                           applying any formatting logic.
        special_types (tuple of type): Objects of this type invoke
                                       .get_value(kwargs) on the object to get
                                       output value during formatting.
    """

    _FORMAT_SPEC_RECURSION_DEPTH = 2

    def __init__(self, passthrough_types=None, special_types=None):
        """Initialize me.

        Args:
            passthrough_types (tuple of type): Objects of this type do not
                                               format at all - pass through
                                               without applying any formatting
                                               logic. If single type, no need
                                               to put it in tuple.
            special_types (tuple of type): Objects of this type invoke
                                           .get_value on the instance to get
                                           output value during formatting. If
                                           single type, no need to put it in
                                           tuple.
        """
        self.passthrough_types = passthrough_types
        self.special_types = special_types

    def format(self, format_string, *args, **kwargs):
        """Format the input with arbitrary positional & keyword args.

        Use exactly as you would in string.Formatter. Only you get 'ff' & 'rf'
        extra.

        format_string can be any type, not just string. If format_string
        contains an iterable object, will iterate through it recursively and
        apply formatting on all strings as it goes.
        """
        return self.vformat(format_string, args, kwargs)

    def vformat(self, format_string, args, kwargs):
        """Format the input with predefined dict of args.

        Use exactly as you would in string.Formatter. Only you get 'ff' & 'rf'
        extra.

        Use me to avoid unpacking & repacking the dict as individual args
        using the *args & **kwargs syntax of .format().

        format_string can be any type, not just string. If format_string
        contains an iterable object, will iterate through it recursively and
        apply formatting on all strings as it goes.

        Args:
            format_string (object): Any object to format.
            args (iterable): Variable list positional args for formatting
                             expression.
            kwargs (iterable): Variable mapping of keyword args for formatting
                               expression.
        """
        used_args = set()
        result = self._get_formatted_iterable(format_string,
                                              args,
                                              kwargs,
                                              used_args)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def _format_keep_type(self, format_string, args, kwargs, used_args,
                          recursion_depth, auto_arg_index=0,
                          is_recursive=False):
        """Do the actual implementation for formatting formattable objects.

        Don't call me directly. Use format() or vformat().

        The logic is largely poached from the python string.Formatter
        _vformat() method, with thanks!

        Args:
            format_string (object): Any object to format.
            args (iterable): Variable list positional args for formatting
                             expression.
            kwargs (iterable): Variable mapping of keyword args for formatting
                               expression.
            used_args (set): Mutating set of args used during formatting.
            recursion_depth (int): Only used if format_spec has formatting
                                   itself.
            auto_arg_index (int): Only used if format_spec has formatting
                                  itself.
            is_recursive (bool): Used internally to specify that
                                 in an active recursion loop where the parent
                                 indicated recursion. This is to allow nested
                                 formatting expressions to recurse themselves
                                 by default.
        """
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        result = []
        for literal_text, field_name, format_spec, conversion in \
                self.parse(format_string):

            # output the literal text
            if literal_text:
                result.append((literal_text, True, None))

            # if there's a field, output it
            if field_name is not None:
                # handle arg indexing when empty field_names are given.
                if field_name == '':
                    if auto_arg_index is False:
                        raise ValueError('cannot switch from manual field '
                                         'specification to automatic field '
                                         'numbering')
                    field_name = str(auto_arg_index)
                    auto_arg_index += 1
                elif field_name.isdigit():
                    if auto_arg_index:
                        raise ValueError('cannot switch from manual field '
                                         'specification to automatic field '
                                         'numbering')
                    # disable auto arg incrementing, if it gets
                    # used later on, then an exception will be raised
                    auto_arg_index = False

                # given the field_name, find the object it references
                # and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)

                # expand the format spec, if needed.
                # format spec expansion uses standard formatting of base class.
                format_spec, auto_arg_index = self._vformat(
                    format_spec, args, kwargs,
                    used_args, recursion_depth - 1,
                    auto_arg_index=auto_arg_index)

                # not doing this in format_field because need to know whether
                # to recurse or not here already - format_field doesn't take
                # the args/kwargs that get_formatted_iterable needs.
                recursion_spec = RecursionSpec(format_spec)

                # the resulting object could be formattable itself
                if recursion_spec.is_recursive or (
                        is_recursive and not recursion_spec.is_flat):
                    obj = self._get_formatted_iterable(
                        obj, args, kwargs, used_args, None, True)
                    recursion_spec.has_recursed = True

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # only decide whether to format once sure that this is a
                # string and not a single object. thus, add to list, deal with
                # that after this field iteration completes.
                result.append((obj, False, recursion_spec))

        # where input is '{expr}' - i.e comprised entirely of 1 expression,
        # return the result object WITHOUT casting to string.
        if len(result) == 1:
            # single object. don't format for literals.
            obj, is_literal, recursion_spec = result[0]
            if is_literal:
                return obj
            else:
                if not (recursion_spec.has_recursed or recursion_spec.is_flat):
                    # default is go recursive on special case where there's a
                    # single formatting expression comprising the entire string
                    obj = self._get_formatted_iterable(
                        obj, args, kwargs, used_args, None,
                        recursion_spec.is_recursive)

                # if format_spec explicitly specified, can assume caller DOES
                # want the string conversion that format_spec does.
                if recursion_spec.format_spec:
                    return self.format_field(obj, recursion_spec.format_spec)
                else:
                    # do not format so retain the type
                    return obj

        else:
            # it must be a string with multiple formatting expressions in it
            return ''.join([obj
                            if is_literal
                            else self.format_field(obj,
                                                   recursion_spec.format_spec)
                            for obj, is_literal, recursion_spec in result])

    def _get_formatted_iterable(self, obj, args, kwargs, used_args, memo=None,
                                is_recursive=False):
        """Format any type of object & do so recursively if it's an iterable.

        Interpolates strings from the input args & kwargs.

        This is not a full on deepcopy, and it's on purpose not a full on
        deepcopy. It will handle dict, list, set, tuple for iteration, without
        any especial cuteness for other types or types not derived from these.

        A formattable object is a string or a special_type.

        special_type will call .get_value(kwargs) on the instance instead of
        formatting via the standard formatter.

        For iterable types, iterates recursively and formats all formattable
        objects in the iterable. Mappings will format both key and value.

        For any other type of object: returns it as is.

        This is what formatting or interpolating a string means:
        So where a string like this 'Piping {key1} the {key2} wild'
        And args/kwargs={'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}

        Then this will return string: "Piping down the valleys wild"

        special_type will call .get_value(kwargs) on the instance instead of
        formatting via the standard formatter.

        Args:
            obj (any type): Recurse through me and format strings found in
                            iterables. Does not mutate the input object.
            args (iterable): Variable list positional args for formatting
                             expression.
            kwargs (iterable): Variable mapping of keyword args for formatting
                               expression.
            used_args (set): Mutating set of args used during formatting.
            memo (dict): Don't use. Used internally on recursion to optimize
                         recursive loops.
            is_recursive (bool): Don't use. Used internally to specify that
                                 in an active recursion loop.

        Returns:
            The input object formatted, if that object was a string or
            special_type. If the input obj was an iterable, an iterable
            identical in structure to the input, except where formatting
            changed a value from a string or special type to the formatting
            expression's evaluated value.

        """
        if memo is None:
            memo = {}

        obj_id = id(obj)
        already_done = memo.get(obj_id, None)
        if already_done is not None:
            return already_done

        # order important. passthrough supersedes special supersedes str.
        if self.passthrough_types and isinstance(obj, self.passthrough_types):
            new = obj
        elif self.special_types and isinstance(obj, self.special_types):
            new = obj.get_value(kwargs)
        elif isinstance(obj, str):
            new = self._format_keep_type(
                obj, args, kwargs, used_args,
                recursion_depth=self._FORMAT_SPEC_RECURSION_DEPTH,
                is_recursive=is_recursive)
        elif isinstance(obj, (bytes, bytearray)):
            new = obj
        elif isinstance(obj, Mapping):
            # dicts
            new = obj.__class__(
                (
                    self._get_formatted_iterable(
                        k, args, kwargs, used_args, memo, is_recursive),
                    self._get_formatted_iterable(
                        v, args, kwargs, used_args, memo, is_recursive)
                )
                for k, v in obj.items()
            )
        elif isinstance(obj, (Sequence, Set)):
            # list, set, tuple. Bytes and str won't fall into this branch coz
            # they're explicitly checked further up in the if.
            new = obj.__class__(
                self._get_formatted_iterable(
                    v, args, kwargs, used_args, memo, is_recursive)
                for v in obj)
        else:
            # int, float, bool, function, et.
            return obj

        # If is its own copy, don't memoize.
        if new is not obj:
            memo[obj_id] = new

        return new
