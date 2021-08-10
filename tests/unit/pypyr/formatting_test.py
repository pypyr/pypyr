"""formatting.py unit tests."""
from unittest.mock import Mock
import pytest
from pypyr.formatting import RecursionSpec, RecursiveFormatter

# region recursion_spec


def test_recursion_spec_empty():
    """Empty recursion spec initializes defaults."""
    r = RecursionSpec('')
    r.has_recursed = False
    r.is_flat = False
    r.is_recursive = False
    r.is_set = False
    r.format_spec = ''


def test_recursion_spec_no_match():
    """Input without special recursion indicators."""
    r = RecursionSpec('ABCD')
    r.has_recursed = False
    r.is_flat = False
    r.is_recursive = False
    r.is_set = False
    r.format_spec = 'ABCD'


def test_recursion_spec_no_match_less_than_two():
    """Short input without special recursion indicators."""
    r = RecursionSpec('a')
    r.has_recursed = False
    r.is_flat = False
    r.is_recursive = False
    r.is_set = False
    r.format_spec = 'a'


def test_recursion_spec_flat():
    """Parse flat recursion spec."""
    r = RecursionSpec('ff')
    r.has_recursed = False
    r.is_flat = True
    r.is_recursive = False
    r.is_set = True
    r.format_spec = ''


def test_recursion_spec_flat_with_extra():
    """Parse flat recursion spec with extra spec following."""
    r = RecursionSpec('ffabcd')
    r.has_recursed = False
    r.is_flat = True
    r.is_recursive = False
    r.is_set = True
    r.format_spec = 'abcd'


def test_recursion_spec_recursive():
    """Parse recursive recursion spec."""
    r = RecursionSpec('rf')
    r.has_recursed = False
    r.is_flat = False
    r.is_recursive = True
    r.is_set = True
    r.format_spec = ''


def test_recursion_spec_recursive_with_extra():
    """Parse recursive recursion spec with extra spec following."""
    r = RecursionSpec('rfabcd')
    r.has_recursed = False
    r.is_flat = False
    r.is_recursive = True
    r.is_set = True
    r.format_spec = 'abcd'

# endregion recursion_spec

# region RecursiveFormatter

# region RecursiveFormatter.format


def test_recursive_formatter_format_none():
    """Format a None."""
    formatter = RecursiveFormatter()
    assert formatter.format(None, 'a', 'b', 'c') is None


def test_recursive_formatter_format_empty():
    """Format an empty string."""
    formatter = RecursiveFormatter()
    assert formatter.format('', 'a', 'b', 'c') == ''


def test_recursive_formatter_format_no_expression():
    """Format a string sans formatting expression."""
    formatter = RecursiveFormatter()
    assert formatter.format('arb string', 'a', 'b', 'c') == 'arb string'


def test_recursive_formatter_format_args():
    """Format a string with positional args."""
    formatter = RecursiveFormatter()
    assert (formatter.format('{0} arb {1} string', 'a', 'b', 'c')
            == 'a arb b string')


def test_recursive_formatter_format_args_no_index():
    """Format a string with positional args and auto index."""
    formatter = RecursiveFormatter()
    assert (formatter.format('{} arb {} string', 'a', 'b', 'c')
            == 'a arb b string')


def test_recursive_formatter_format_kwargs():
    """Format a string with kwargs."""
    formatter = RecursiveFormatter()
    assert (formatter.format('{b} arb {c} string', a='a', b='b', c='c')
            == 'b arb c string')


def test_recursive_formatter_format_args_and_kwargs():
    """Format a string with positional args and kwargs."""
    formatter = RecursiveFormatter()
    assert (formatter.format('{} and {b} arb {c} string', 'a', b='b', c='c')
            == 'a and b arb c string')


def test_recursive_formatter_manual_to_auto():
    """Can't switch from manual to auto field numbering."""
    with pytest.raises(ValueError) as err:
        RecursiveFormatter().format('{0} {}', 'a', 'b')

    assert (str(err.value)
            == ('cannot switch from manual field specification to automatic '
                'field numbering'))


def test_recursive_formatter_auto_to_manual():
    """Can't switch from manual to auto field numbering."""
    with pytest.raises(ValueError) as err:
        RecursiveFormatter().format('{} {1}', 'a', 'b')

    assert (str(err.value)
            == ('cannot switch from manual field specification to automatic '
                'field numbering'))

# endregion RecursiveFormatter.format

# region RecursiveFormatter.vformat


def test_recursive_formatter_vformat_none():
    """None is None."""
    assert RecursiveFormatter().vformat(None, (1, 2), {'a': 'b'}) is None


def test_recursive_formatter_vformat_literal():
    """Literal only."""
    assert RecursiveFormatter().vformat('literal here',
                                        (1, 2),
                                        {'a': 'b'}
                                        ) == 'literal here'


def test_recursive_formatter_vformat_literal_end():
    """Literal at end."""
    assert RecursiveFormatter().vformat('{} literal here',
                                        (1, 2),
                                        {'a': 'b'}
                                        ) == '1 literal here'


def test_recursive_formatter_vformat_literal_start():
    """Literal at start."""
    assert RecursiveFormatter().vformat('literal here {a}',
                                        (1, 2),
                                        {'a': 'b'}
                                        ) == 'literal here b'


def test_recursive_formatter_vformat_literal_middle():
    """Literal in middle."""
    assert RecursiveFormatter().vformat('{} literal here {a}',
                                        (1, 2),
                                        {'a': 'b'}
                                        ) == '1 literal here b'


def test_recursive_formatter_vformat_no_literal():
    """No literal, only formatting expressions."""
    assert RecursiveFormatter().vformat('{0}{1}{a}',
                                        (1, 2),
                                        {'a': 'b'}
                                        ) == '12b'


def test_recursive_formatter_vformat_default():
    """Default formatting is standard flat."""
    d = {
        'one': '1',
        'two': '2 {one} 2',
        'three': '3 {two} 3'
    }
    assert RecursiveFormatter().vformat('start {three} end',
                                        None,
                                        d
                                        ) == 'start 3 {two} 3 end'


def test_recursive_formatter_vformat_default_with_formatting():
    """Default formatting is flat & standard formatting expression works."""
    d = {
        'one': '1',
        'two': '2 {one} 2',
        'three': '3 {two} 3'
    }
    assert RecursiveFormatter().vformat('start {three:+>11} end',
                                        None,
                                        d
                                        ) == 'start ++3 {two} 3 end'


def test_recursive_formatter_vformat_default_with_formatting_conversion():
    """Flat & standard formatting expression works with conversion."""
    d = {
        'one': '1',
        'two': '2 {one} 2',
        'three': [0, 1, '{two}']
    }
    assert RecursiveFormatter().vformat('start {three!s:+>17} end',
                                        None,
                                        d
                                        ) == "start ++[0, 1, '{two}'] end"


def test_recursive_formatter_vformat_flat():
    """Explicit flat formatting."""
    d = {
        'one': '1',
        'two': '2 {one} 2',
        'three': '3 {two} 3'
    }
    assert RecursiveFormatter().vformat('start {three:ff} end',
                                        None,
                                        d
                                        ) == 'start 3 {two} 3 end'


def test_recursive_formatter_vformat_recursive():
    """Explicit recursive formatting."""
    d = {
        'one': '1',
        'two': '2 {one} 2',
        'three': '3 {two} 3'
    }
    assert RecursiveFormatter().vformat('start {three:rf} end',
                                        None,
                                        d
                                        ) == 'start 3 2 1 2 3 end'


def test_recursive_formatter_vformat_rf_to_ff():
    """Explicit recursive formatting until ff, where it stops."""
    d = {
        'one': '1',
        'two': '2 {one} 2',
        'three': '3 {two:ff} 3'
    }
    assert RecursiveFormatter().vformat('start {three:rf} end',
                                        None,
                                        d
                                        ) == 'start 3 2 {one} 2 3 end'


def test_recursive_formatter_vformat_single_default():
    """Default formatting is for single expression is recursive."""
    d = {
        'one': '1',
        'two': '{one}',
        'three': '{two}'
    }
    assert RecursiveFormatter().vformat('{three}', None, d) == '1'


def test_recursive_formatter_vformat_single_flat():
    """Explicit flat formatting on single expression."""
    d = {
        'one': '1',
        'two': '{one}',
        'three': '{two}'
    }
    assert RecursiveFormatter().vformat('{three:ff}', None, d) == '{two}'


def test_recursive_formatter_vformat_single_recursive():
    """Explicit recursive formatting on single formatting."""
    d = {
        'one': '1',
        'two': '{one}',
        'three': '{two}'
    }
    assert RecursiveFormatter().vformat('{three:rf}', None, d) == '1'


def test_recursive_formatter_vformat_single_rf_to_ff():
    """Explicit recursive formatting on single formatting stops at ff."""
    d = {
        'one': '1',
        'two': '{one}',
        'three': '{two:ff}'
    }
    assert RecursiveFormatter().vformat('{three:rf}', None, d) == '{one}'


def test_recursive_formatter_vformat_single_default_to_ff():
    """Default recursive formatting on single formatting stops at ff."""
    d = {
        'one': '1',
        'two': '{one}',
        'three': '{two:ff}'
    }
    assert RecursiveFormatter().vformat('{three}', None, d) == '{one}'


def test_recursive_formatter_vformat_single_default_keep_type():
    """Default formatting for single expression is recursive & keeps type."""
    d = {
        'one': 1,
        'two': '{one}',
        'three': '{two}'
    }
    assert RecursiveFormatter().vformat('{three}', None, d) == 1


def test_recursive_formatter_vformat_single_default_with_conversion():
    """Single expression is recursive & conversion works."""
    d = {
        'one': 1,
        'two': '{one}',
        'three': '{two}'
    }
    assert RecursiveFormatter().vformat('{three!r:rf}', None, d) == '1'


def test_recursive_formatter_vformat_single_default_with_formatting():
    """Single expression is recursive & extra standard formatting works."""
    d = {
        'one': 1,
        'two': '{one}',
        'three': '{two}'
    }
    assert RecursiveFormatter().vformat('{three:rf+>3}', None, d) == '++1'


def test_recursive_formatter_vformat_with_passthrough():
    """Passthrough types do not format."""
    d = {
        'one': 1,
        'two': '{one}',
        'three': '{two}'
    }

    assert RecursiveFormatter(passthrough_types=str).vformat('{three}',
                                                             None,
                                                             d
                                                             ) == '{three}'


def test_recursive_formatter_vformat_with_passthrough_tuple():
    """Multiple passthrough types do not format."""
    d = {
        'one': 1,
        'two': '{one}',
        'three': {'{one}': '{two}'},
        'four': ['{one}', 'arb']
    }

    formatter = RecursiveFormatter(passthrough_types=(dict, list))
    assert formatter.vformat('{three}', None, d) == {'{one}': '{two}'}
    assert formatter.vformat(d['four'], None, d) == ['{one}', 'arb']


def test_recursive_formatter_vformat_with_special_type():
    """Special types call get_value."""
    special = Mock()
    special.get_value = Mock(return_value=123)

    d = {
        'one': 1,
        'two': special,
        'three': '{two}'
    }

    assert RecursiveFormatter(special_types=Mock).vformat('{three}',
                                                          None,
                                                          d
                                                          ) == 123
    special.get_value.assert_called_once_with(d)


class MyString(str):
    """Arbitrary test class."""

    def __new__(cls, p_string):
        """Create new class so works like string."""
        return str.__new__(cls, p_string)

    def get_value(self, kwargs):
        """Arbitrary kwargs."""
        return f'123 {kwargs["arbkey"]}'


class MyStringDerived(str):
    """Arbitrary class derived from MyString."""

    def get_value(self, kwargs):
        """Arbitrary kwargs."""
        return f'XXX {kwargs["arbkey"]}'


def test_recursive_formatter_vformat_with_special_tuple():
    """Multiple special types call get_value and supersedes string."""
    special = Mock()
    special.get_value = Mock(return_value=123)

    my_string = MyString('blah')

    d = {
        'one': 1,
        'two': special,
        'three': '{two}',
        'arbkey': 456,
        'my_string': my_string
    }

    format_me = {
        'k1': '{three}',
        'k2': '{my_string}'}

    formatter = RecursiveFormatter(special_types=(Mock, MyString))

    assert formatter.vformat(format_me,
                             None,
                             d
                             ) == {'k1': 123,
                                   'k2': '123 456'}
    special.get_value.assert_called_once_with(d)
    assert my_string == 'blah'


def test_recursive_formatter_iterate_list():
    """Recurse through a list."""
    special = Mock()
    special.get_value = Mock(return_value=123)

    my_string = MyString('blah')
    my_string_derived = MyStringDerived('blah derived')

    d = {
        'one': 1,
        'two': special,
        'three': '{two}',
        'arbkey': 456,
        'my_string': my_string,
        'my_string_derived': my_string_derived
    }

    repeating_item = Mock()
    repeating_item.get_value = Mock(return_value=999)

    passthrough_derived_obj = ValueError('arb')

    input_obj = [
        repeating_item,
        'literal string',
        'string {one} expression',
        repeating_item,
        passthrough_derived_obj,
        special,
        '{my_string}',
        MyStringDerived,
        set([1, 2, 3, 4, '{arbkey}']),
        [5, 6, 7],
        {'a': 'b', '{one}': MyStringDerived},
        b'\x00\x10',
        890,
        1.13
    ]

    formatter = RecursiveFormatter(passthrough_types=(Exception,
                                                      MyStringDerived),
                                   special_types=(Mock, MyString))
    out = formatter.vformat(input_obj, None, d)

    assert out == [
        999,
        'literal string',
        'string 1 expression',
        999,
        passthrough_derived_obj,
        123,
        '123 456',
        MyStringDerived,
        {1, 2, 3, 4, 456},
        [5, 6, 7],
        {'a': 'b', 1: MyStringDerived},
        b'\x00\x10',
        890,
        1.13
    ]

# endregion RecursiveFormatter.vformat

# region format_spec nesting


def test_recursive_formatter_recurse_format_spec():
    """Recurse on format_spec works."""
    d = {
        'k1': 'x',
        'k2': 123
    }
    assert RecursiveFormatter().vformat("a {k2:{k1}} b", None, d) == 'a 7b b'


def test_recursive_formatter_recurse_format_spec_double():
    """Recurse on format_spec exceeding max double replace."""
    d = {
        'align': '>',
        'fill': '+',
        'k3': 123
    }
    assert RecursiveFormatter().vformat(
        "a {k3:{fill}{align}5} b", None, d) == 'a ++123 b'


def test_recursive_formatter_recurse_format_spec_max_exceeded():
    """Recurse on format_spec exceeding max raises."""
    d = {
        'dash': '-',
        'i': 5,
        'align': '>',
        'fill': '+',
        'k3': 123
    }

    with pytest.raises(ValueError) as err:
        RecursiveFormatter().vformat("a {k3:{fill}{align}{i:{dash}}} b",
                                     None, d)

    assert str(err.value) == 'Max string recursion exceeded'


def test_recursive_format_keep_type_recurse_format_spec_max_exceeded():
    """Recurse on format_spec exceeding max raises.

    This test is a bit arb. Strictly speaking the recursion_depth check here
    won't be hit by any implemented code, because format_spec recursion goes
    through the standard _vformat and not _format_keep_type.

    But derived classes might. So leave a test in anyway.
    """
    d = {
        'dash': '-',
        'i': 5,
        'align': '>',
        'fill': '+',
        'k3': 123
    }

    with pytest.raises(ValueError) as err:
        RecursiveFormatter()._format_keep_type(
            "a {k3:{fill}{align}{i:{dash}}} b",
            None, d, set(), -1)

    assert str(err.value) == 'Max string recursion exceeded'

# endregion format_spec nesting

# region RecursiveFormatter.check_used_arguments


class UnusedArgs(RecursiveFormatter):
    """Unused Args test class."""

    def __init__(self, expected):
        """In expected is what used_args should be."""
        super().__init__()
        self.expected = expected

    def check_unused_args(self, used_args, args, kwargs):
        """Intercept used_args for test against expected."""
        assert used_args == self.expected


def test_recursive_formatter_unused_args():
    """Unused args as expected."""
    formatter = UnusedArgs({0, 1})
    assert (formatter.format('{} arb {} string', 'a', 'b', 'c')
            == 'a arb b string')


def test_recursive_formatter_unused_args_none():
    """Unused args as expected when all unused."""
    formatter = UnusedArgs(set())
    assert formatter.format('arb string', 'a', 'b', 'c') == 'arb string'


def test_recursive_formatted_unused_rf():
    """Unused keeps track of used args during recursion."""
    formatter = UnusedArgs({'k2', 'k3'})
    d = {
        'k1': 'v1',
        'k2': 'v2',
        'k3': [
            1,
            2,
            {'k3.1': '3.1 value {k2}'}
        ]
    }
    assert (formatter.vformat('a {k3[2][k3.1]:rf} b', None, d)
            == "a 3.1 value v2 b")


def test_recursive_formatted_unused_one_expression():
    """Unused keeps track of used args during recursion on 1 expression."""
    formatter = UnusedArgs({'k1', 'k2', 'k3'})
    d = {
        'k1': 'v1',
        'k2': '{k1}',
        'k3': [
            1,
            2,
            {'k3.1': '{k2}'}
        ]
    }
    assert (formatter.vformat('{k3[2][k3.1]}', None, d)
            == 'v1')

# endregion RecursiveFormatter.check_used_arguments

# endregion RecursiveFormatter
