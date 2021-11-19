"""context.py unit tests."""
import builtins
from collections.abc import MutableMapping
import pickle
import typing

import pytest

from pypyr.context import Context, ContextItemInfo
from pypyr.dsl import PyString, SicString
from pypyr.errors import (
    ContextError,
    KeyInContextHasNoValueError,
    KeyNotInContextError)
from pypyr.pipeline import Pipeline

# region behaves like a dictionary


def test_context_is_dictionary_like():
    """Context should behave like a dictionary."""
    # initializes to empty
    d = Context()
    assert d is not None
    # len is not a given on custom implementations
    assert len(d) == 0

    # dict ctor "just works"
    d = Context({'k1': 'v1', 'k2': 'v2'})
    assert d
    assert len(d) == 2
    assert d['k1'] == 'v1'
    assert d['k2'] == 'v2'

    # __set_item__ assignment add and update works
    d['k1'] = 'value 1'
    d['k2'] = 'value 2'
    d['k3'] = ['one list', 'two list', 'three list']
    d['k4'] = {'kk1': 'vv1', 'kk2': 'vv2', 'kk3': 'vv3'}
    d['k5'] = True
    d['k6'] = ('thing', False, ['1', '2', '3'], 6)
    d['k7'] = 77

    assert d['k5']

    # isinstance resolves to dict - this test might become invalid if refactor
    # to a MutableMapping custom object
    assert isinstance(d, dict)
    assert isinstance(d, MutableMapping)
    assert len(d) == 7

    # items() can iterate
    for k, v in d.items():
        if k == 'k4':
            assert isinstance(v, dict)

        if k == 'k6':
            assert isinstance(v, tuple)

    # values() can iterate
    for v in d.values():
        assert v

    # __get_item__ works
    assert d['k1'] == 'value 1'

    # update merging works
    mergedic = {'k1': 'NEWVALUE'}
    d.update(mergedic)
    assert d['k1'] == 'NEWVALUE'

    # del and clear
    original_length = len(d)
    del d['k1']
    assert 'k1' not in d
    assert len(d) == original_length - 1

    d.clear()
    assert len(d) == 0


def test_context_init_and_eq_like_dict():
    """Context construct in all the ways a dict can."""
    a = Context(one=1, two=2, three=3)
    b = Context({'one': 1, 'two': 2, 'three': 3})
    c = Context(zip(['one', 'two', 'three'], [1, 2, 3]))
    d = Context([('two', 2), ('one', 1), ('three', 3)])
    e = Context({'three': 3, 'one': 1, 'two': 2})
    f = Context({'one': 1, 'three': 3}, two=2)
    assert a == b == c == d == e == f
    assert a == {'one': 1, 'two': 2, 'three': 3}


def test_context_init_instance():
    """Context constructor adds instance attributes."""
    # builtins_only = {'__builtins__': builtins.__dict__}
    assert Context()._pystring_globals == {}
    context = Context(a=1,
                      b=2,
                      len='123')

    # the underlying dict has builtins.
    assert list(dict.items(context._pystring_namespace)) == [
        ('__builtins__', builtins.__dict__)]
    # the chainmap has the user-space globals
    assert context._pystring_namespace.maps == [{'a': 1,
                                                 'b': 2,
                                                 'len': '123'},
                                                {}]

    # context supersedes globals
    assert context.get_eval_string('len') == '123'


def test_context_missing_override():
    """Subclass of dict should override __missing__ on KeyNotFound."""
    context = Context({'arbkey': 'arbvalue'})

    with pytest.raises(KeyNotInContextError):
        context['notindict']


def test_context_missing_raise_key_error():
    """Context should raise error compatible with dict KeyError."""
    context = Context({'arbkey': 'arbvalue'})

    with pytest.raises(KeyError):
        context['notindict']


def test_context_pickles():
    """Context survives a pickle."""
    og = Context(a='b', c='e f')

    og.pystring_globals_update(g='h')

    dumped = pickle.dumps(og)

    assert len(og._pystring_namespace) == 3
    assert og._pystring_namespace['c'] == 'e f'
    assert og._pystring_globals == {'g': 'h'}

    reloaded = pickle.loads(dumped)

    assert og._pystring_globals == {'g': 'h'}
    assert len(og._pystring_namespace) == 3
    assert og._pystring_namespace['c'] == 'e f'

    assert type(reloaded) is Context
    assert reloaded.current_pipeline is None
    assert not reloaded._stack
    assert reloaded == {'a': 'b', 'c': 'e f'}
    assert reloaded._pystring_globals == {'g': 'h'}
    assert list(dict.items(reloaded._pystring_namespace)) == [
        ('__builtins__', builtins.__dict__)]
    assert reloaded._pystring_namespace.maps == [{'a': 'b',
                                                  'c': 'e f'},
                                                 {'g': 'h'}]
    assert reloaded.get_formatted_value('f{a}') == 'fb'
    assert reloaded.get_eval_string('len(c)') == 3


# endregion behaves like a dictionary

# region asserts


def test_assert_child_key_has_value_passes():
    """Pass if [parent][child] has value."""
    context = Context({
        'parent': {
            'child': 1
        }
    })

    context.assert_child_key_has_value('parent', 'child', 'arb')


def test_assert_child_key_has_value_raises_no_parent():
    """Raise if [parent] doesn't exist."""
    context = Context({
        'parent': {
            'child': 1
        }
    })

    with pytest.raises(KeyNotInContextError):
        context.assert_child_key_has_value('XparentX', 'child', 'arb')


def test_assert_child_key_has_value_raises_no_child():
    """Raise if [parent][child] doesn't exist."""
    context = Context({
        'parent': {
            'child': 1
        }
    })

    with pytest.raises(KeyNotInContextError) as err:
        context.assert_child_key_has_value('parent', 'XchildX', 'arb')

    assert str(err.value) == (
        "context['parent']['XchildX'] doesn't exist. It must exist for arb.")


def test_assert_child_key_has_value_raises_child_none():
    """Raise if [parent][child] is None."""
    context = Context({
        'parent': {
            'child': None
        }
    })

    with pytest.raises(KeyInContextHasNoValueError) as err:
        context.assert_child_key_has_value('parent', 'child', 'arb')

    assert str(err.value) == (
        "context['parent']['child'] must have a value for arb.")


def test_assert_child_key_has_value_raises_parent_none():
    """Raise if [parent] is None."""
    context = Context({
        'parent': None
    })

    with pytest.raises(KeyInContextHasNoValueError) as err:
        context.assert_child_key_has_value('parent', 'child', 'arb')

    assert str(err.value) == ("context['parent'] must have a value for arb.")


def test_assert_child_key_has_value_raises_parent_not_iterable():
    """Raise if [parent] is not iterable."""
    context = Context({
        'parent': 1
    })

    with pytest.raises(ContextError) as err:
        context.assert_child_key_has_value('parent', 'child', 'arb')

    assert str(err.value) == ("context['parent'] must exist, be iterable and "
                              "contain 'child' for arb. argument of type 'int'"
                              " is not iterable")


def test_assert_key_exists_raises():
    """Raise KeyNotInContextError if key doesn't exist."""
    context = Context({'key1': 'value1'})
    with pytest.raises(KeyNotInContextError):
        context.assert_key_exists('notindict', None)


def test_assert_key_exists_passes_value_none():
    """assert_key_has_value passes if context dictionary key value is None."""
    context = Context({'key1': None})
    context.assert_key_exists('key1', None)


def test_assert_key_exists_passes_string_values():
    """assert_key_has_value passes if context dictionary key value is None."""
    context = Context({'key1': 'something', 'key2': 'other', 'key3': False})
    context.assert_key_exists('key2', None)
    context.assert_key_exists('key3', None)


def test_assert_keys_exist_passes():
    """Pass if list of keys all found in context dictionary."""
    context = Context({'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})
    context.assert_keys_exist(None, 'key1', 'key3')


def test_assert_keys_exists_with_values_fails():
    """Raise KeyNotInContextError if list of keys not all found in context."""
    with pytest.raises(KeyNotInContextError):
        context = Context({'key1': 'value1',
                           'key2': 'value2',
                           'key3': 'value3'})
        context.assert_keys_exist(None,
                                  'key1',
                                  'key4',
                                  'key2',
                                  )


def test_assert_key_has_value_fails_on_context_empty():
    """Expect KeyNotInContextError if context empty."""
    context = Context()
    with pytest.raises(KeyNotInContextError):
        context.assert_key_has_value('key', 'desc')


def test_assert_key_has_value_on_key_none():
    """Pass if assert key is None."""
    context = Context({None: 'value1'})
    context.assert_key_has_value(None, None)


def test_assert_key_has_value_fails_key_not_found():
    """Raise KeyNotInContextError if context doesn't have key on assert."""
    context = Context({'key1': 'value1'})
    with pytest.raises(KeyNotInContextError):
        context.assert_key_has_value('notindict', None)


def test_assert_key_has_value__empty():
    """No KeyNotInContextError if key exists but value empty (not None)."""
    context = Context({'key': ''})
    # with pytest.raises(KeyNotInContextError):
    context.assert_key_has_value('key', None)


def test_assert_key_has_value_fails_key_error_message():
    """Raise KeyNotInContextError if missing key, assert message correct."""
    context = Context({'key1': 'value1'})
    with pytest.raises(KeyNotInContextError) as err_info:
        context.assert_key_has_value('notindict', 'mydesc')

    assert str(err_info.value) == ("context['notindict'] "
                                   "doesn't exist. It must exist for "
                                   "mydesc.")


def test_assert_key_has_value_fails_key_empty():
    """Raise KeyInContextHasNoValueError if context dict key value is None."""
    context = Context({'key1': None})
    with pytest.raises(KeyInContextHasNoValueError):
        context.assert_key_has_value('key1', None)


def test_assert_key_has_value_passes():
    """Pass if key_in_dict_has_value dictionary key has value."""
    context = Context({'key1': 'value1'})
    context.assert_key_has_value('key1', None)


def test_assert_key_has_bool_true_passes():
    """Pass if key_in_dict_has_value dictionary key has bool True value."""
    context = Context({'key1': True})
    context.assert_key_has_value('key1', None)


def test_assert_key_has_bool_false_passes():
    """Pass if key_in_dict_has_value dictionary key has bool False value."""
    context = Context({'key1': False})
    context.assert_key_has_value('key1', None)


def test_assert_keys_have_values_passes():
    """Pass if list of keys all found in context dictionary."""
    context = Context({'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})
    context.assert_keys_have_values(None, 'key1', 'key3')


def test_assert_keys_have_values_fails():
    """Raise KeyNotInContextError if list of keys don't all have values."""
    with pytest.raises(KeyNotInContextError):
        context = Context({'key1': 'value1',
                           'key2': 'value2',
                           'key3': 'value3'})
        context.assert_keys_have_values(None,
                                        'key1',
                                        'key4',
                                        'key2',
                                        )


def test_assert_key_type_value_passes():
    """assert_key_type_value passes if key exists, has value and type right."""
    info = ContextItemInfo(key='key1',
                           key_in_context=True,
                           expected_type=str,
                           is_expected_type=True,
                           has_value=True)

    Context().assert_key_type_value(info, None)


def test_assert_key_type_value_no_key_raises():
    """assert_key_type_value fails if key doesn't exist."""
    info = ContextItemInfo(key='key1',
                           key_in_context=False,
                           expected_type=str,
                           is_expected_type=True,
                           has_value=True)

    with pytest.raises(KeyNotInContextError) as err_info:
        Context().assert_key_type_value(info, 'mydesc')

    assert str(err_info.value) == "mydesc couldn't find key1 in context."


def test_assert_key_type_value_no_key_raises_extra_text():
    """assert_key_type_value fails if key doesn't exist."""
    info = ContextItemInfo(key='key1',
                           key_in_context=False,
                           expected_type=str,
                           is_expected_type=True,
                           has_value=True)

    with pytest.raises(KeyNotInContextError) as err_info:
        Context().assert_key_type_value(info, 'mydesc', 'extra text here')

    assert str(err_info.value) == (
        "mydesc couldn't find key1 in context. extra text here")


def test_assert_key_type_value_no_value_raises():
    """assert_key_type_value fails if no value."""
    info = ContextItemInfo(key='key1',
                           key_in_context=True,
                           expected_type=str,
                           is_expected_type=True,
                           has_value=False)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        Context().assert_key_type_value(info, 'mydesc')

    assert str(err_info.value) == ("mydesc found key1 in context but it "
                                   "doesn\'t have a value.")


def test_assert_key_type_value_no_value_raises_extra_text():
    """assert_key_type_value fails if no value."""
    info = ContextItemInfo(key='key1',
                           key_in_context=True,
                           expected_type=str,
                           is_expected_type=True,
                           has_value=False)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        Context().assert_key_type_value(info, 'mydesc', 'extra text here')

    assert str(err_info.value) == ("mydesc found key1 in context but it "
                                   "doesn\'t have a value. extra text here")


def test_assert_key_type_value_wrong_type_raises():
    """assert_key_type_value fails if wrong type."""
    info = ContextItemInfo(key='key1',
                           key_in_context=True,
                           expected_type=str,
                           is_expected_type=False,
                           has_value=True)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        Context().assert_key_type_value(info, 'mydesc')

    assert str(err_info.value) == ("mydesc found key1 in context, but "
                                   "it\'s not a <class 'str'>.")


def test_assert_key_type_value_wrong_type_raises_with_extra_error_text():
    """assert_key_type_value fails if wrong type."""
    info = ContextItemInfo(key='key1',
                           key_in_context=True,
                           expected_type=str,
                           is_expected_type=False,
                           has_value=True)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        Context().assert_key_type_value(info, 'mydesc', 'extra text here')

    assert str(err_info.value) == (
        "mydesc found key1 in context, but "
        "it\'s not a <class 'str'>. extra text here")


def test_assert_keys_type_value_passes():
    """assert_keys_type_value passes if all keys, types, values correct."""
    info1 = ContextItemInfo(key='key1',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    info2 = ContextItemInfo(key='key2',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    info3 = ContextItemInfo(key='key3',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    Context().assert_keys_type_value(None, '', info1, info2, info3)


def test_assert_keys_type_value_raises():
    """assert_keys_type_value raises if issue with one in the middle."""
    info1 = ContextItemInfo(key='key1',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    info2 = ContextItemInfo(key='key2',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=False)

    info3 = ContextItemInfo(key='key3',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        Context().assert_keys_type_value('mydesc', None, info1, info2, info3)

    assert str(err_info.value) == ("mydesc found key2 in context but it "
                                   "doesn\'t have a value.")


def test_assert_keys_type_value_raises_with_extra_error_text():
    """assert_keys_type_value raises if issue with one in the middle."""
    info1 = ContextItemInfo(key='key1',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    info2 = ContextItemInfo(key='key2',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=False)

    info3 = ContextItemInfo(key='key3',
                            key_in_context=True,
                            expected_type=str,
                            is_expected_type=True,
                            has_value=True)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        Context().assert_keys_type_value('mydesc',
                                         'extra text here',
                                         info1,
                                         info2,
                                         info3)

    assert str(err_info.value) == ("mydesc found key2 in context but it "
                                   "doesn\'t have a value. extra text here")

# endregion asserts

# region get_eval


def test_get_eval_string_bool():
    """Bool eval."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = 'key1 == \'down\''
    output = context.get_eval_string(input_string)
    assert isinstance(output, bool)
    assert output


def test_get_eval_string_builtins():
    """Built-in on eval."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = 'len(key1)'
    assert context.get_eval_string(input_string) == 4


def test_get_eval_string_empty():
    """Empty string raises."""
    with pytest.raises(ValueError) as err:
        assert Context().get_eval_string('')

    assert str(err.value) == ('input expression is empty. It must be a valid '
                              'python expression instead.')


def test_get_eval_string_none():
    """None string raises."""
    with pytest.raises(ValueError) as err:
        assert Context().get_eval_string(None)

    assert str(err.value) == ('input expression is empty. It must be a valid '
                              'python expression instead.')


def test_get_eval_string_with_globals():
    """Eval with globals set."""
    import math
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context.pystring_globals_update({'mymath': math})
    input_string = 'mymath.sqrt(len(key1))'
    assert context.get_eval_string(input_string) == 2

    # context unaffected - eval didn't add a builtins anywhere
    assert context == {'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}
    assert context._pystring_globals == {'mymath': math}
    assert list(dict.items(context._pystring_namespace)) == [
        ('__builtins__', builtins.__dict__)]
    assert context._pystring_namespace.maps == [context,
                                                {'mymath': math}]


def test_get_eval_simple_expr_context_empty():
    """Simple expression passes, with empty context."""
    assert Context().get_eval_string('1+1') == 2


def test_get_eval_simple_expr_with_builtins():
    """Simple expression passes, with empty context."""
    out = Context().get_eval_string('len("123456") < 5')
    assert isinstance(out, bool)
    assert not out

    assert Context({'k1': 'v1'}).get_eval_string('len([0,1,2])') == 3


def test_get_eval_simple_expr_with_import():
    """Simple expression passes, with stdlib import."""
    context = Context()
    from math import sqrt as mysqrt
    context.pystring_globals_update(sqrt=mysqrt)
    assert context.get_eval_string('sqrt(4)') == 2


def test_get_eval_expr_context_vars():
    """Expression uses vars from context."""
    assert Context({'k1': 2, 'k2': 3}).get_eval_string('(k1 + k2)*2==10')


def test_get_eval_expr_context_nested_vars():
    """Expression uses nested vars from input dict."""
    assert Context({'k1': 1,
                    'k2': [0,
                           1,
                           {'k2.2': 1.23}
                           ]
                    }).get_eval_string('k2[2]["k2.2"] == 1.23')


def test_get_eval_expr_evals_bool():
    """Expression can work as a boolean type."""
    out = Context({'a': True}).get_eval_string('a')
    assert isinstance(out, bool)
    assert out


def test_get_eval_expr_evals_locals_empty():
    """Check existence in locals when empty context."""
    out = Context().get_eval_string("'a' in locals()")
    assert out is False


def test_get_eval_expr_evals_locals_contains():
    """Check existence in locals."""
    out = Context({'a': 'b'}).get_eval_string("'a' in locals()")
    assert out is True


def test_get_eval_expr_evals_globals_contains():
    """Check existence in globals."""
    out = Context({'a': 'b'}).get_eval_string("'a' in globals()")
    assert out is True


def test_get_eval_expr_evals_dir_contains():
    """Check existence in dir."""
    out = Context({'a': 'b'}).get_eval_string("'a' in dir()")
    assert out is True


def test_get_eval_expr_evals_vars_contains():
    """Check existence in vars."""
    out = Context({'a': 'b'}).get_eval_string("'a' in vars()")
    assert out is True


def test_get_eval_expr_evals_vars_contains_false():
    """Check existence in vars."""
    out = Context({'a': 'b'}).get_eval_string("'b' in vars()")
    assert out is False


def test_get_eval_expr_evals_vars_empty():
    """Check existence in vars."""
    out = Context().get_eval_string("'b' in vars()")
    assert out is False


def test_get_eval_expr_evals_complex():
    """Expression evaluates complex types."""
    assert Context({'c': {'a': 'b'}}).get_eval_string('{"a": "b"} == c')


def test_get_eval_expr_runtime_error():
    """Expression raises expected type during runtime error."""
    with pytest.raises(ZeroDivisionError):
        Context().get_eval_string('1/0')


def test_get_eval_expr_invalid_syntax():
    """Expression raises when invalid syntax on input."""
    with pytest.raises(SyntaxError):
        Context().get_eval_string('invalid code here')


def test_get_eval_expr_var_doesnt_exist():
    """Expression raises when variable not found in namespace."""
    with pytest.raises(NameError):
        Context({'b': True}).get_eval_string('a')


def test_get_eval_expr_builtins_imports_and_context():
    """Expression evaluates with builtin, imported namespace and context."""
    context = Context({'a': 1, 'b': 2})
    from math import ceil as myceil
    context.pystring_globals_update({'ceil': myceil})
    assert context.get_eval_string('a+b + ceil(b) + abs(-1)') == 6


def test_get_eval_expr_only_globals():
    """Expression evaluates with only globals."""
    context = Context()
    context.pystring_globals_update({'a': 11, 'b': 22})
    assert context.get_eval_string('abs(a+b)') == 33


def test_get_eval_nested_scopes():
    """Free variables and comprehension nested scopes."""
    context = Context({'list1': [0, 1],
                       'list2': ['a', 'b']})
    eval_me = '[(x, y) for x in list1 for y in list2]'
    assert context.get_eval_string(eval_me) == [(0, 'a'), (0, 'b'),
                                                (1, 'a'), (1, 'b')]


class ArbClassForEvalTest():
    """Arb test class."""

    a = 123

    def __init__(self):
        """Arb init."""
        self.b = 456

    def dothing(self, val):
        """Arb test method."""
        return ArbClassForEvalTest.a + val

    @ classmethod
    def dothing_class_method(cls, val):
        """Arb class method."""
        return cls.a - val

    @ staticmethod
    def dothing_static_method(val):
        """Arb static method."""
        return val + 2


def test_get_eval_class():
    """Arbitrary class with instance, static and class attributes."""
    context = Context({'c': 789})
    context.pystring_globals_update({'A': ArbClassForEvalTest})

    assert context.get_eval_string('A.a') == 123
    assert context.get_eval_string('A().b') == 456
    assert context.get_eval_string('A().dothing(1)') == 124
    assert context.get_eval_string('A.dothing_class_method(1)') == 122
    assert context.get_eval_string('A.dothing_static_method(1) + c') == 792

    # none of this mutated context
    assert context == {'c': 789}

# endregion get_eval

# region formats


def test_string_interpolate_works():
    """Interpolate works."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping {key1} the {key2} wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_works_with_no_swaps():
    """Interpolate no swap."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping down the valleys wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_escapes_double_curly():
    """Interpolate double curly escape."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping {{ down the valleys wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping { down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_escapes_double_curly_pair():
    """Interpolate double double curly."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping {{down}} the valleys wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping {down} the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_sic():
    """Interpolate ignore sic."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = SicString("Piping {key1} the {key2} wild")
    output = context.get_formatted('input_string')
    assert output == 'Piping {key1} the {key2} wild', (
        "string interpolation incorrect")


def test_string_interpolate_py():
    """Interpolate do py."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = PyString("len(key1) + len(key2)")
    output = context.get_formatted('input_string')
    assert output == 11, (
        "string interpolation incorrect")


def test_single_curly_should_throw():
    """Interpolate single curly raise."""
    with pytest.raises(ValueError):
        context = Context({'key1': 'value1'})
        context['input_string'] = '{key1} this { is {key2} string'
        context.get_formatted('input_string')


def test_tag_not_in_context_should_throw():
    """Interpolate key not in context raises."""
    with pytest.raises(KeyNotInContextError) as err:
        context = Context({'key1': 'value1'})
        context['input_string'] = '{key1} this is {key2} string'
        context.get_formatted('input_string')

    assert str(err.value) == (
        "Unable to format '{key1} this is "
        "{key2} string' at context['input_string'], because "
        "key2 not found in the pypyr context.")


def test_context_item_not_a_string_should_return_as_is():
    """Interpolate non-string."""
    context = Context({'key1': 'value1'})
    context['input_string'] = 77
    val = context.get_formatted('input_string')
    assert val == 77


def test_context_item_list_should_iterate():
    """Interpolate iterable."""
    context = Context({'key1': 'value1'})
    context['input_string'] = ['string1', '{key1}', 'string3']
    val = context.get_formatted('input_string')
    assert val == ['string1', 'value1', 'string3']


def test_input_string_interpolate_works():
    """Interpolate strings."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = 'Piping {key1} the {key2} wild'
    output = context.get_formatted_value(input_string)
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_input_string_tag_not_in_context_should_throw():
    """Interpolate not in context."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'key1': 'value1'})
        input_string = '{key1} this is {key2} string'
        context.get_formatted_value(input_string)

    assert str(err_info.value) == "key2 not found in the pypyr context."


def test_input_string_interpolate_sic():
    """Interpolate sic."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = SicString("Piping {key1} the {key2} wild")
    output = context.get_formatted_value(input_string)
    assert output == "Piping {key1} the {key2} wild", (
        "string interpolation incorrect")


def test_input_string_interpolate_sic_singlequote():
    """Interpolate sic with quotes."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = SicString('Piping {key1} the {key2} wild')
    output = context.get_formatted_value(input_string)
    assert output == "Piping {key1} the {key2} wild", (
        "string interpolation incorrect")


def test_input_string_interpolate_py_singlequote():
    """Interpolate py single quotes."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = PyString('len(key1) * len(key2)')
    output = context.get_formatted_value(input_string)
    assert output == 28, (
        "string interpolation incorrect")


def test_input_string_not_a_string_on_interpolate_return_og():
    """Interpolate returns original if not string."""
    context = Context({'key1': 'value1'})
    assert 77 == context.get_formatted_value(77)


def test_get_formatted_iterable_list():
    """Simple list."""
    input_obj = ['k1', 'k2', '{ctx3}', True, False, 44]

    context = Context(
        {'ctx1': 'ctxvalue1', 'ctx2': 'ctxvalue2', 'ctx3': 'ctxvalue3'})

    output = context.get_formatted_value(input_obj)

    assert output is not input_obj
    assert output[0] == 'k1'
    assert output[1] == 'k2'
    assert output[2] == 'ctxvalue3'
    assert output[3]
    assert not output[4]
    assert output[5] == 44


def test_get_formatted_iterable_tuple():
    """Simple tuple."""
    input_obj = ('k1', 'k2', '{ctx3}', True, False, 44)

    context = Context(
        {'ctx1': 'ctxvalue1', 'ctx2': 'ctxvalue2', 'ctx3': 'ctxvalue3'})

    output = context.get_formatted_value(input_obj)

    assert output is not input_obj
    assert output[0] == 'k1'
    assert output[1] == 'k2'
    assert output[2] == 'ctxvalue3'
    assert output[3]
    assert not output[4]
    assert output[5] == 44


def test_get_formatted_iterable_set():
    """Simple set."""
    input_obj = {'k1', 'k2', '{ctx3}', True, False, 44}

    context = Context(
        {'ctx1': 'ctxvalue1', 'ctx2': 'ctxvalue2', 'ctx3': 'ctxvalue3'})

    output = context.get_formatted_value(input_obj)

    assert output is not input_obj
    assert len(output) == len(input_obj)
    diffs = output - input_obj
    assert len(diffs) == 1
    assert 'ctxvalue3' in diffs


def test_get_formatted_immutable_mapping():
    """Simple read-only mapping test."""

    class ReadOnlyMapping(typing.Mapping):
        def __init__(self, *args, **kwargs):
            self._data = dict(*args, **kwargs)

        def __getitem__(self, key):
            return self._data[key]

        def __len__(self):
            return len(self._data)

        def __iter__(self):
            return iter(self._data)

    input_obj = {'key': '{ctx}'}

    context = Context(
        {'ctx': ReadOnlyMapping({'arb': 1})})

    output = context.get_formatted_value(input_obj)

    assert output is not input_obj
    assert isinstance(output['key'], ReadOnlyMapping)
    assert output['key'] == {'arb': 1}


def test_get_formatted_iterable_nested():
    """Straight deepish copy with no formatting."""
    # dict containing dict, list, dict-list-dict, tuple, dict-tuple-list
    input_obj = {'k1': 'v1',
                 'k2': 'v2',
                 'k3': 'v3',
                 'k4': [
                     1,
                     2,
                     '3here',
                     {'key4.1': 'value4.1',
                      'key4.2': 'value4.2',
                      'key4.3': {
                          '4.3.1': '4.3.1value',
                          '4.3.2': '4.3.2value'}}
                 ],
                 'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                 'k6': ('six6.1', False, [0, 1, 2], 77, 'sixend'),
                 'k7': 'simple string to close 7'
                 }

    context = Context(
        {'ctx1': 'ctxvalue1', 'ctx2': 'ctxvalue2', 'ctx3': 'ctxvalue3'})

    output = context.get_formatted_value(input_obj)

    assert output == input_obj
    assert output is not context
    # verify this was a deep copy - obj refs has to be different for nested
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][3]['key4.3']) != id(input_obj['k4'][3]['key4.3'])
    assert id(output['k5']) != id(input_obj['k5'])
    assert id(output['k6']) != id(input_obj['k6'])
    assert id(output['k6'][2]) != id(input_obj['k6'][2])
    assert id(output['k7']) == id(input_obj['k7'])

    # and proving the theory: mutating output does not touch input
    assert output['k4'][1] == 2
    output['k4'][1] = 88
    assert input_obj['k4'][1] == 2
    assert output['k4'][1] == 88


def test_get_formatted_iterable_nested_with_formatting():
    """Straight deepish copy with formatting."""
    # dict containing dict, list, dict-list-dict, tuple, dict-tuple-list, bytes
    input_obj = {'k1': 'v1',
                 'k2': 'v2_{ctx1}',
                 'k3': bytes('v3{ctx1}', encoding='utf-8'),
                 'k4': [
                     1,
                     2,
                     '3_{ctx4}here',
                     {'key4.1': 'value4.1',
                      '{ctx2}_key4.2': 'value_{ctx3}_4.2',
                      'key4.3': {
                          '4.3.1': '4.3.1value',
                          '4.3.2': '4.3.2_{ctx1}_value'}}
                 ],
                 'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                 'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
                 'k7': 'simple string to close 7'
                 }

    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4'})

    output = context.get_formatted_value(input_obj)

    assert output != input_obj

    # verify formatted strings
    assert input_obj['k2'] == 'v2_{ctx1}'
    assert output['k2'] == 'v2_ctxvalue1'

    assert input_obj['k3'] == b'v3{ctx1}'
    assert output['k3'] == b'v3{ctx1}'

    assert input_obj['k4'][2] == '3_{ctx4}here'
    assert output['k4'][2] == '3_ctxvalue4here'

    assert input_obj['k4'][3]['{ctx2}_key4.2'] == 'value_{ctx3}_4.2'
    assert output['k4'][3]['ctxvalue2_key4.2'] == 'value_ctxvalue3_4.2'

    assert input_obj['k4'][3]['key4.3']['4.3.2'] == '4.3.2_{ctx1}_value'
    assert output['k4'][3]['key4.3']['4.3.2'] == '4.3.2_ctxvalue1_value'

    assert input_obj['k6'][4] == 'six_{ctx1}_end'
    assert output['k6'][4] == 'six_ctxvalue1_end'

    # verify this was a deep copy - obj refs has to be different for nested
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][3]['key4.3']) != id(input_obj['k4'][3]['key4.3'])
    assert id(output['k5']) != id(input_obj['k5'])
    assert id(output['k6']) != id(input_obj['k6'])
    assert id(output['k6'][2]) != id(input_obj['k6'][2])
    # strings are interned in python, so id is the same
    assert id(output['k7']) == id(input_obj['k7'])
    output['k7'] = 'mutate 7 on new'
    assert input_obj['k7'] == 'simple string to close 7'
    assert output['k7'] == 'mutate 7 on new'


def test_get_formatted_iterable_nested_with_sic():
    """Straight deepish copy with formatting."""
    # dict containing dict, list, dict-list-dict, tuple, dict-tuple-list, bytes
    input_obj = {'k1': 'v1',
                 'k2': 'v2_{ctx1}',
                 'k3': bytes('v3{ctx1}', encoding='utf-8'),
                 'k4': [
                     1,
                     2,
                     '3_{ctx4}here',
                     {'key4.1': 'value4.1',
                      '{ctx2}_key4.2': SicString("value_{ctx3}_4.2"),
                      'key4.3': {
                          '4.3.1': '4.3.1value',
                          '4.3.2': '4.3.2_{ctx1}_value'}}
                 ],
                 'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                 'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
                 'k7': 'simple string to close 7'
                 }

    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4'})

    output = context.get_formatted_value(input_obj)

    assert output != input_obj

    # verify formatted strings
    assert input_obj['k2'] == 'v2_{ctx1}'
    assert output['k2'] == 'v2_ctxvalue1'

    assert input_obj['k3'] == b'v3{ctx1}'
    assert output['k3'] == b'v3{ctx1}'

    assert input_obj['k4'][2] == '3_{ctx4}here'
    assert output['k4'][2] == '3_ctxvalue4here'

    assert input_obj['k4'][3]['{ctx2}_key4.2'] == SicString("value_{ctx3}_4.2")
    assert output['k4'][3]['ctxvalue2_key4.2'] == 'value_{ctx3}_4.2'

    assert input_obj['k4'][3]['key4.3']['4.3.2'] == '4.3.2_{ctx1}_value'
    assert output['k4'][3]['key4.3']['4.3.2'] == '4.3.2_ctxvalue1_value'

    assert input_obj['k6'][4] == 'six_{ctx1}_end'
    assert output['k6'][4] == 'six_ctxvalue1_end'

    # verify this was a deep copy - obj refs has to be different for nested
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][3]['key4.3']) != id(input_obj['k4'][3]['key4.3'])
    assert id(output['k5']) != id(input_obj['k5'])
    assert id(output['k6']) != id(input_obj['k6'])
    assert id(output['k6'][2]) != id(input_obj['k6'][2])
    # strings are interned in python, so id is the same
    assert id(output['k7']) == id(input_obj['k7'])
    output['k7'] = 'mutate 7 on new'
    assert input_obj['k7'] == 'simple string to close 7'
    assert output['k7'] == 'mutate 7 on new'


def test_get_formatted_iterable_non_string_key():
    """Format context with non-strings in keys."""
    input_obj = {'k1': 'v1',
                 'k2': 'v2_{ctx1}',
                 'k3': bytes('v3{ctx1}', encoding='utf-8'),
                 'k4': [
                     1,
                     2,
                     '3_{ctx4}here',
                     {'key4.1': 'value4.1',
                      '{ctx2}_key4.2': SicString("value_{ctx3}_4.2"),
                      'key4.3': {
                          '4.3.1': '4.3.1value',
                          '4.3.2': '4.3.2_{ctx1}_value',
                          7: '4.3.3_{ctx4}_value'}}
                 ],
                 'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                 'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
                 'k7': 'simple string to close 7',
                 6: {7, 89}
                 }

    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4',
         5: [1, 2, 3]})

    output = context.get_formatted_value(input_obj)

    assert output != input_obj
    assert output == {'k1': 'v1',
                      'k2': 'v2_ctxvalue1',
                      'k3': bytes('v3{ctx1}', encoding='utf-8'),
                      'k4': [
                          1,
                          2,
                          '3_ctxvalue4here',
                          {'key4.1': 'value4.1',
                           'ctxvalue2_key4.2': "value_{ctx3}_4.2",
                           'key4.3': {
                               '4.3.1': '4.3.1value',
                               '4.3.2': '4.3.2_ctxvalue1_value',
                               7: '4.3.3_ctxvalue4_value'}}
                      ],
                      'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                      'k6': ('six6.1', False, [0, 1, 2], 77,
                             'six_ctxvalue1_end'),
                      'k7': 'simple string to close 7',
                      6: {7, 89}
                      }


def test_get_formatted_iterable_with_memo():
    """Straight deepish copy with formatting."""
    arb_dict = {'key4.1': 'value4.1',
                '{ctx2}_key4.2': 'value_{ctx3}_4.2',
                'key4.3': {
                    '4.3.1': '4.3.1value',
                    '4.3.2': '4.3.2_{ctx1}_value'}}

    arb_list = [0, 1, 2]

    arb_string = 'arb string'

    arb_string_with_formatting = 'a {ctx1} string'

    input_obj = {'k1': arb_string,
                 'k2': 'v2_{ctx1}',
                 'k3': arb_list,
                 'k4': [
                     arb_dict,
                     2,
                     '3_{ctx4}here',
                     arb_dict
                 ],
                 'k5': {'key5.1': arb_string,
                        'key5.2': arb_string_with_formatting},
                 'k6': ('six6.1', False, arb_list, 77, 'six_{ctx1}_end'),
                 'k7': 'simple string to close 7',
                 'k8': arb_string_with_formatting
                 }

    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4'})

    output = context.get_formatted_value(input_obj)

    # same obj re-used at different levels of the hierarchy
    assert id(input_obj['k3']) == id(input_obj['k6'][2])
    assert id(input_obj['k4'][0]) == id(input_obj['k4'][3])

    assert output != input_obj

    # verify formatted strings
    assert input_obj['k2'] == 'v2_{ctx1}'
    assert output['k2'] == 'v2_ctxvalue1'

    assert input_obj['k4'][2] == '3_{ctx4}here'
    assert output['k4'][2] == '3_ctxvalue4here'

    assert input_obj['k4'][3]['{ctx2}_key4.2'] == 'value_{ctx3}_4.2'
    assert output['k4'][3]['ctxvalue2_key4.2'] == 'value_ctxvalue3_4.2'

    assert input_obj['k4'][3]['key4.3']['4.3.2'] == '4.3.2_{ctx1}_value'
    assert output['k4'][3]['key4.3']['4.3.2'] == '4.3.2_ctxvalue1_value'

    assert input_obj['k6'][4] == 'six_{ctx1}_end'
    assert output['k6'][4] == 'six_ctxvalue1_end'

    # verify this was a deep copy - obj refs has to be different for nested
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][3]['key4.3']) != id(input_obj['k4'][3]['key4.3'])
    assert id(output['k5']) != id(input_obj['k5'])
    assert id(output['k6']) != id(input_obj['k6'])
    assert id(output['k6'][2]) != id(input_obj['k6'][2])
    assert id(output['k7']) == id(input_obj['k7'])
    output['k7'] = 'mutate 7 on new'
    assert input_obj['k7'] == 'simple string to close 7'
    assert input_obj['k8'] == arb_string_with_formatting
    assert output['k8'] == 'a ctxvalue1 string'

    # memo did object re-use so same obj re-used at different levels of the
    # hierarchy
    assert id(output['k3']) == id(output['k6'][2])
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][0]) == id(output['k4'][3])
    assert output['k5']['key5.1'] == input_obj['k5']['key5.1'] == arb_string
    assert id(output['k5']['key5.1']) == id(
        input_obj['k5']['key5.1']) == id(arb_string)
    assert id(output['k8']) == id(output['k5']['key5.2'])
    assert id(output['k8']) != id(arb_string_with_formatting)


def test_iter_formatted():
    """On iter_formatted yields a formatted string on each loop."""
    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4'})

    input_strings = [
        "this {ctx1} is {ctx2} line 1",
        "this is {ctx3} line 2",
        "this is line 3",
        "this {ctx4} is line 4"
    ]

    output = list(context.iter_formatted_strings(input_strings))

    assert output[0] == "this ctxvalue1 is ctxvalue2 line 1"
    assert output[1] == "this is ctxvalue3 line 2"
    assert output[2] == "this is line 3"
    assert output[3] == "this ctxvalue4 is line 4"


def test_get_formatted_as_type_string_to_bool_no_subst():
    """On get_formatted_as_type returns bool no formatting."""
    context = Context()
    result = context.get_formatted_as_type('False', out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_string_to_true_bool_no_subst():
    """On get_formatted_as_type returns bool no formatting."""
    context = Context()
    result = context.get_formatted_as_type('True', out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_false_no_subst():
    """On get_formatted_as_type returns bool no formatting."""
    context = Context()
    result = context.get_formatted_as_type(False, out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_bool_true_no_subst():
    """On get_formatted_as_type returns bool no formatting."""
    context = Context()
    result = context.get_formatted_as_type(None, True, out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_false_with_subst():
    """On get_formatted_as_type returns bool with formatting."""
    context = Context({'k1': False})
    result = context.get_formatted_as_type(None, '{k1}', out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_bool_true_with_subst():
    """On get_formatted_as_type returns bool with formatting."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type(None, '{k1}', out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_true_with_list_input():
    """On get_formatted_as_type returns bool True with arbitrary input."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type([0, 1, 2], out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_false_with_empty_list_input():
    """On get_formatted_as_type returns bool false with empty input."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type([], out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_bool_false_with_0_input():
    """On get_formatted_as_type returns bool False with 0 input."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type(0, out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_bool_false_with_string_capital_false():
    """On get_formatted_as_type returns bool False with string FALSE."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type('FALSE', out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_bool_true_with_1_input():
    """On get_formatted_as_type returns bool True with int 1 input."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type(1, out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_true_with_decimal_input():
    """On get_formatted_as_type returns bool True with decimal input."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type(1.1, out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_true_with_str_true():
    """On get_formatted_as_type returns bool True with string true."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type('true', out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_true_with_str_capital_true():
    """On get_formatted_as_type returns bool True with string TRUE."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type('TRUE', out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_true_with_str_1_true():
    """On get_formatted_as_type returns bool True with string 1."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type('1', out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_true_with_pystring_true():
    """On get_formatted_as_type returns bool True with py string True."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type(PyString('k1 and True'),
                                           out_type=bool)

    assert isinstance(result, bool)
    assert result


def test_get_formatted_as_type_bool_false_with_pystring_false():
    """On get_formatted_as_type returns bool True with py string True."""
    context = Context({'k1': True})
    result = context.get_formatted_as_type(PyString('not k1'), out_type=bool)

    assert isinstance(result, bool)
    assert not result


def test_get_formatted_as_type_int_no_subst():
    """On get_formatted_as_type returns int no formatting."""
    context = Context()
    result = context.get_formatted_as_type('10', out_type=int)

    assert isinstance(result, int)
    assert result == 10


def test_get_formatted_as_type_int_with_subst():
    """On get_formatted_as_type returns int no formatting."""
    context = Context({'k1': 10})
    result = context.get_formatted_as_type('{k1}', out_type=int)

    assert isinstance(result, int)
    assert result == 10


def test_get_formatted_as_type_float_no_subst():
    """On get_formatted_as_type returns float no formatting."""
    context = Context()
    result = context.get_formatted_as_type('10.1', out_type=float)

    assert isinstance(result, float)
    assert result == 10.1


def test_get_formatted_as_type_default_no_subst():
    """On get_formatted_as_type returns default no formatting."""
    context = Context()
    result = context.get_formatted_as_type(None, default=10, out_type=int)

    assert isinstance(result, int)
    assert result == 10


def test_get_formatted_as_type_default_with_subst():
    """On get_formatted_as_type returns default with formatting."""
    context = Context({'k1': 10})
    result = context.get_formatted_as_type(
        None, default='{k1}', out_type=int)

    assert isinstance(result, int)
    assert result == 10


def test_get_formatted_as_type_default_with_subst_str():
    """On get_formatted_as_type returns default with formatting."""
    context = Context({'k1': 10})
    result = context.get_formatted_as_type(
        None, default='xx{k1}xx')

    assert isinstance(result, str)
    assert result == 'xx10xx'


def test_get_formatted_value_string():
    """Format input strings."""
    context = Context({'k1': 10})
    assert context.get_formatted_value('{k1}') == 10


def test_get_formatted_value_int():
    """Format input int."""
    context = Context({'k1': 10})
    assert context.get_formatted_value(11) == 11


def test_get_formatted_value_pystring():
    """Format input pystring."""
    context = Context({'k1': 10})
    out = context.get_formatted_value(PyString('11'))
    assert out == 11
    assert isinstance(out, int)


def test_get_formatted_value_bool():
    """Format input int."""
    context = Context({'k1': 10})
    assert not context.get_formatted_value(False)


def test_get_formatted_value_dict():
    """Format input dict."""
    context = Context({'k1': 10})
    assert context.get_formatted_value({'{k1}', 12}) == {10, 12}


def test_get_formatted_value_list():
    """Format input list."""
    context = Context({'k1': 10})
    assert context.get_formatted_value(['{k1}', 12, 13]) == [10, 12, 13]


def test_get_processed_string_no_interpolation():
    """On get_processed_string on plain string returns plain."""
    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4'})

    input_string = 'test string here'

    output = context.get_formatted_value(input_string)

    assert input_string == output


def test_get_processed_string_with_interpolation():
    """Process string with interpolation."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = 'Piping {key1} the {key2} wild'
    output = context.get_formatted_value(input_string)
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_get_processed_string_bare_interpolation():
    """Process string with interpolation with bare expression."""
    context = Context({'k': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = '{k}'
    output = context.get_formatted_value(input_string)
    assert output == 'down', (
        "string interpolation incorrect")


def test_get_processed_string_shorter_than_6_no_interpolation():
    """Process string with no interpolation."""
    context = Context()
    input_string = 'k'
    output = context.get_formatted_value(input_string)
    assert output == 'k', (
        "string interpolation incorrect")


def test_get_processed_string_sic_skips_interpolation():
    """Process string with sic interpolation."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = SicString("Piping {key1} the {key2} wild")
    output = context.get_formatted_value(input_string)
    assert output == 'Piping {key1} the {key2} wild', (
        "string interpolation incorrect")


def test_get_processed_string_pystring_double_quote():
    """Process string with double quotes interpolation."""
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = PyString("key1 == 'down'")
    output = context.get_formatted_value(input_string)
    assert isinstance(output, bool)
    assert output


def test_get_processed_string_pystring_single_quote():
    """Process string with py string interpolation."""
    context = Context({'key1': 2, 'key2': -3, 'key3': 'value3'})
    input_string = PyString('abs(key1+key2)')
    output = context.get_formatted_value(input_string)
    assert isinstance(output, int)
    assert output == 1


def test_get_processed_string_single_expression_keeps_type():
    """Process string with interpolation honors type."""
    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': [0, 1, 3],
         'ctx4': 'ctxvalue4'})

    input_string = '{ctx3}'

    output = context.get_formatted_value(input_string)

    assert output == [0, 1, 3]
    assert isinstance(output, list)


def test_get_processed_string_single_expression_keeps_type_and_iterates():
    """Process string with interpolation on iterable."""
    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': [0,
                  {'s1': 'v1',
                   '{ctx1}': '{ctx2}',
                   's3': [0, '{ctx4}']}, 3],
         'ctx4': 'ctxvalue4'})

    input_string = '{ctx3}'

    output = context.get_formatted_value(input_string)

    assert output == [0,
                      {'s1': 'v1',
                       'ctxvalue1': 'ctxvalue2',
                       's3': [0, 'ctxvalue4']}, 3]


def test_get_processed_string_leading_literal():
    """Process string with interpolation leading literal."""
    context = Context({'k': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = 'leading literal{k}'
    output = context.get_formatted_value(input_string)
    assert output == 'leading literaldown', (
        "string interpolation incorrect")


def test_get_processed_string_following_literal():
    """Process string with interpolation literal end."""
    context = Context({'k': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = '{k}following literal'
    output = context.get_formatted_value(input_string)
    assert output == 'downfollowing literal', (
        "string interpolation incorrect")
# endregion formats

# region key info


def test_key_in_context():
    """Assert key in context."""
    context = Context({'k1': 'v1', 'k2': False, 'k3': ['one', 'two']})

    k1, = context.keys_exist('k1')
    assert k1
    k1, k2, k3 = context.keys_exist('k1', 'k2', 'k3')
    assert k1 and k2 and k3

    k4, k2, k1 = context.keys_exist('k4', 'k2', 'k1')
    assert k1 and k2 and not k4


def test_keys_of_type_exist_single():
    """Assert key in context."""
    """return a single tuple."""
    context = Context({'k1': 'v1', 'k2': False, 'k3': ['one', 'two']})

    k1, = context.keys_of_type_exist(('k1', str),)
    assert k1
    assert k1.key == 'k1'
    assert k1.key_in_context
    assert k1.expected_type is str
    assert k1.is_expected_type
    assert k1.has_value


def test_keys_of_type_exist_triple():
    """Assert key in context."""
    context = Context({'k1': 'v1', 'k2': False, 'k3': ['one', 'two']})

    k3, k2, k1 = context.keys_of_type_exist(
        ('k3', list),
        ('k2', list),
        ('k1', str)
    )

    assert k1
    assert k1.key == 'k1'
    assert k1.key_in_context
    assert k1.expected_type is str
    assert k1.is_expected_type
    assert k1.has_value

    assert k2
    assert k2.key == 'k2'
    assert k2.key_in_context
    assert k2.expected_type is list
    assert not k2.is_expected_type
    assert k2.has_value

    assert k3
    assert k3.key == 'k3'
    assert k3.key_in_context
    assert k3.expected_type is list
    assert k3.is_expected_type
    assert k3.has_value


def test_keys_none_exist():
    """Assert key not in context."""
    context = Context({'k1': 'v1', 'k2': False, 'k3': ['one', 'two']})

    k4, = context.keys_of_type_exist(
        ('k4', list)
    )

    k5, k6 = context.keys_of_type_exist(
        ('k5', bool),
        ('k6', list),
    )

    assert k4
    assert k4.key == 'k4'
    assert not k4.key_in_context
    assert k4.expected_type is list
    assert k4.is_expected_type is None
    assert not k4.has_value

    assert k5
    assert k5.key == 'k5'
    assert not k5.key_in_context
    assert k5.expected_type is bool
    assert k5.is_expected_type is None
    assert not k5.has_value

    assert k6
    assert k6.key == 'k6'
    assert not k6.key_in_context
    assert k6.expected_type is list
    assert k6.is_expected_type is None
    assert not k6.has_value

# endregion key info

# region merge


def test_merge_pass_no_substitutions():
    """Merge success case with no substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        6: 6
    })

    add_me = {
        'key2': 'value4',
        'key4': 'value5'
    }

    context.merge(add_me)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value4'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value5'
    assert context[6] == 6


def test_merge_pass_nested_with_substitutions():
    """Merge success case with nested hierarchy and substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': {
            'k31': 'value31',
            'k32': 'value32',
        },
        'key5': False,
        15: 16
    })

    add_me = {
        'key2': 'value4',
        'key3': {
            'k33': 'value33'
        },
        'key4': '444_{key1}_444',
        'key5': {
            'k51': PyString('key1')
        },
        13: 14,
        15: 17
    }

    context.merge(add_me)

    assert context == {
        'key1': 'value1',
        'key2': 'value4',
        'key3': {
            'k31': 'value31',
            'k32': 'value32',
            'k33': 'value33'
        },
        'key4': '444_value1_444',
        'key5': {
            'k51': 'value1'
        },
        13: 14,
        15: 17
    }


def test_merge_pass_no_recognized_type():
    """Merge success case where type not known mergable."""
    arb_obj = TimeoutError('blah')
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': {
            'k31': 'value31',
            'k32': 'value32',
        },
        'key5': TimeoutError('boom')})

    add_me = {
        'key2': 'value4',
        'key3': {
            'k33': 'value33'
        },
        'key4': '444_{key1}_444',
        'key5': arb_obj
    }

    context.merge(add_me)

    assert context == {
        'key1': 'value1',
        'key2': 'value4',
        'key3': {
            'k31': 'value31',
            'k32': 'value32',
            'k33': 'value33'
        },
        'key4': '444_value1_444',
        'key5': arb_obj
    }


def test_merge_pass_nested_with_types():
    """Merge success case with nested hierarchy, substitutions, diff types."""
    context = Context({
        'k1': 'v1',
        'k2': 'v2_{ctx1}',
        'k3': bytes('v3{ctx1}', encoding='utf-8'),
        'k4': [
            1,
            2,
            '3_{ctx4}here',
            {'key4.1': 'value4.1',
             '{ctx2}_key4.2': 'value_{ctx3}_4.2',
             'key4.3': {
                              '4.3.1': '4.3.1value',
                              '4.3.2': '4.3.2_{ctx1}_value'}}
        ],
        'k5': {'key5.1': {'kv511': 'value5.1'}, 'key5.2': 'value5.2'},
        'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
        'k7': 'simple string to close 7',
        'k8': ('tuple1', 'tuple2'),
        'k9': {'set1', 'set2'},
        'k10': (
            1,
            2,
            {'10.1': '10.1v',
             '10.2': '{10.2v}',
             },
            3),
        'k11': {
            'k11.1': '11.1v',
            'k11.2': {
                'k11.2.1': '11.2.1v',
                'k11.2.2': {
                    'k11.2.2.1': '11.2.2.1v'
                },
            },
        },
        'k12': 'end'
    }
    )

    add_me = {
        'k4': [
            4.4,
            {'key4.3': {
                '4.3.1': 'merged value for 4.3.1'
            }
            }
        ],
        'k5': {
            'key5.1': {
                'kv522': 'kv522 from merge {k1}'
            }},
        'k8': ('tuple3', ),
        'k9': {'set3', },
        'k10': ({
            '{k1}': [0,
                     1,
                     2,
                     (
                         'tuple in list in dict in tuple in dict',
                         'hello {k2}',
                         {'k1': '{k1}'}
                     ),
                     [0, 1, 2, '{k1}', 3, (True, False), ['00', '{k1}']],
                     4]
        },
            4),
        'k11': {
            'k11.2': {
                'k11.2.2': {
                    'add me': '{k1}'
                },
            },
        },
    }

    context.merge(add_me)

    assert context == {
        'k1': 'v1',
        'k2': 'v2_{ctx1}',
        'k3': bytes('v3{ctx1}', encoding='utf-8'),
        'k4': [
            1,
            2,
            '3_{ctx4}here',
            {'key4.1': 'value4.1',
             '{ctx2}_key4.2': 'value_{ctx3}_4.2',
             'key4.3': {
                              '4.3.1': '4.3.1value',
                              '4.3.2': '4.3.2_{ctx1}_value'}},
            4.4,
            {'key4.3': {
                '4.3.1': 'merged value for 4.3.1'
            }
            }

        ],
        'k5': {
            'key5.1': {
                'kv511': 'value5.1',
                'kv522': 'kv522 from merge v1'
            },
            'key5.2': 'value5.2'},
        'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
        'k7': 'simple string to close 7',
        'k8': ('tuple1', 'tuple2', 'tuple3'),
        'k9': {'set1', 'set2', 'set3'},
        'k10': (
            1,
            2,
            {'10.1': '10.1v',
             '10.2': '{10.2v}',
             },
            3,
            {'v1': [0,
                    1,
                    2,
                    (
                        'tuple in list in dict in tuple in dict',
                        'hello v2_{ctx1}',
                        {'k1': 'v1'}
                    ),
                    [0, 1, 2, 'v1', 3, (True, False), ['00', 'v1']],
                    4]
             },
            4
        ),
        'k11': {
            'k11.1': '11.1v',
            'k11.2': {
                'k11.2.1': '11.2.1v',
                'k11.2.2': {
                    'k11.2.2.1': '11.2.2.1v',
                    'add me': 'v1'
                },
            },
        },
        'k12': 'end'
    }


def test_merge_interpolate_py():
    """Merge with interpolate."""
    context = Context()
    context.merge({"key": PyString("True")})
    assert context["key"] is True


def test_merge_replaced_by_interpolated_py_mapping():
    """Merge with interpolate py string."""
    context = Context({'key': {'b': 2}})
    context.merge({"key": PyString("{'a': 1}")})
    assert context["key"] == {'a': 1}


def test_merge_interpolate_py_with_substitutions():
    """Merge with interpolate substitutions."""
    context = Context({"key": False})
    context.merge({"key": PyString("5")})
    assert context["key"] == 5


def test_merge_non_string_keys():
    """Merge when key is not string."""
    context = Context({1: False, 2: 'two', 3: '{two}'})
    context.merge({2: 'merged'})
    assert context == {1: False, 2: 'merged', 3: '{two}'}


def test_merge_key_substitutions():
    """Merge when keys substitute."""
    context = Context({'k1': 'v1', 'k2': 'k1', 'k3': 'value3'})
    context.merge({'{k2}': 'newvalue', '{k1}': 'k1merged', '{k3}': '3new'})
    # notice that k1 resolves to newvalue because it evaluates after k2 merge.
    assert context == {'k1': 'newvalue',
                       'k2': 'k1',
                       'newvalue': 'k1merged',
                       'k3': 'value3',
                       'value3': '3new'}


# endregion merge

# region set_defaults


def test_set_defaults_pass_no_substitutions():
    """Defaults success case with no substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
    })

    add_me = {
        'key2': 'value4',
        'key4': 'value5'
    }

    context.set_defaults(add_me)

    assert context['key1'] == 'value1'
    # since key2 exists already, shouldn't update
    assert context['key2'] == 'value2'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value5'


def test_set_defaults_pass_nested_with_substitutions():
    """Merge success case with nested hierarchy and substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': {
            'k31': 'value31',
            'k32': 'value32',
        }})

    add_me = {
        'key2': 'value4',
        'key3': {
            'k33': 'value33'
        },
        'key4': '444_{key1}_444'
    }

    context.set_defaults(add_me)

    assert context == {
        'key1': 'value1',
        'key2': 'value2',
        'key3': {
            'k31': 'value31',
            'k32': 'value32',
            'k33': 'value33'
        },
        'key4': '444_value1_444'
    }


def test_set_defaults_pass_nested_with_types():
    """Defaults with nested hierarchy, substitutions, diff types."""
    context = Context({
        'k1': 'v1',
        'k2': 'v2_{ctx1}',
        'k3': bytes('v3{ctx1}', encoding='utf-8'),
        'k4': [
            1,
            2,
            '3_{ctx4}here',
            {'key4.1': 'value4.1',
             '{ctx2}_key4.2': 'value_{ctx3}_4.2',
             'key4.3': {
                              '4.3.1': '4.3.1value',
                              '4.3.2': '4.3.2_{ctx1}_value'}}
        ],
        'k5': {'key5.1': {'kv511': 'value5.1'}, 'key5.2': 'value5.2'},
        'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
        'k7': 'simple string to close 7',
        'k8': ('tuple1', 'tuple2'),
        'k9': {'set1', 'set2'},
        'k10': (
            1,
            2,
            {'10.1': '10.1v',
             '10.2': '{10.2v}',
             },
            3),
        'k11': {
            'k11.1': '11.1v',
            'k11.2': {
                'k11.2.1': '11.2.1v',
                'k11.2.2': {
                    'k11.2.2.1': '11.2.2.1v'
                },
            },
        },
        'k12': 'end'
    }
    )

    add_me = {
        'k4': [
            4.4,
            {'key4.3': {
                '4.3.1': 'merged value for 4.3.1'
            }
            }
        ],
        'k5': {
            'key5.1': {
                'kv522': 'kv522 from merge {k1}'
            }},
        'k8': ('tuple3', ),
        'k9': {'set3', },
        'k10': ({
            '{k1}': [0,
                     1,
                     2,
                     (
                         'tuple in list in dict in tuple in dict',
                         'hello {k2}',
                         {'k1': '{k1}'}
                     ),
                     [0, 1, 2, '{k1}', 3, (True, False), ['00', '{k1}']],
                     4]
        },
            4),
        'k11': {
            'k11.2': {
                'k11.2.2': {
                    'add me': '{k1}'
                },
            },
        },
    }

    context.set_defaults(add_me)

    assert context == {
        'k1': 'v1',
        'k2': 'v2_{ctx1}',
        'k3': bytes('v3{ctx1}', encoding='utf-8'),
        'k4': [
            1,
            2,
            '3_{ctx4}here',
            {'key4.1': 'value4.1',
             '{ctx2}_key4.2': 'value_{ctx3}_4.2',
             'key4.3': {
                              '4.3.1': '4.3.1value',
                              '4.3.2': '4.3.2_{ctx1}_value'}}
        ],
        'k5': {'key5.1': {'kv511': 'value5.1',
                          'kv522': 'kv522 from merge v1'},
               'key5.2': 'value5.2'},
        'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
        'k7': 'simple string to close 7',
        'k8': ('tuple1', 'tuple2'),
        'k9': {'set1', 'set2'},
        'k10': (
            1,
            2,
            {'10.1': '10.1v',
             '10.2': '{10.2v}',
             },
            3),
        'k11': {
            'k11.1': '11.1v',
            'k11.2': {
                'k11.2.1': '11.2.1v',
                'k11.2.2': {
                    'k11.2.2.1': '11.2.2.1v',
                    'add me': 'v1'
                },
            },
        },
        'k12': 'end'
    }

# endregion set_defaults

# region pipeline_scope


def test_pipeline_scope_stack():
    """Pipeline scope appends/pops Pipeline on the stack."""
    context = Context()

    pipe1 = Pipeline('pipe1')

    assert not context.is_in_pipeline_scope
    assert context.get_stack_depth() == 0
    with context.pipeline_scope(pipe1):
        assert context.current_pipeline.name == 'pipe1'
        assert type(context.current_pipeline) is Pipeline
        assert context.is_in_pipeline_scope
        assert context.get_stack_depth() == 1

        pipe2 = Pipeline('pipe2')

        with context.pipeline_scope(pipe2):
            assert context.current_pipeline.name == 'pipe2'
            assert type(context.current_pipeline) is Pipeline
            assert context.get_root_pipeline().name == 'pipe1'
            assert type(context.get_root_pipeline()) is Pipeline
            assert context.is_in_pipeline_scope
            assert context.get_stack_depth() == 2

        assert context.current_pipeline.name == 'pipe1'
        assert context.is_in_pipeline_scope
        assert context.get_stack_depth() == 1

    assert context.current_pipeline is None
    assert not context.is_in_pipeline_scope
    assert context.get_stack_depth() == 0


def test_get_current_pipeline_no_scope():
    """The current_pipeline is None when not in scope."""
    context = Context()

    assert not context.current_pipeline

    assert context.is_in_pipeline_scope is False
    assert context.get_stack_depth() == 0


def test_get_root_pipeline_no_scope():
    """Get root pipeline info raises ContextError when not in scope."""
    context = Context()

    with pytest.raises(ContextError):
        context.get_root_pipeline()

    assert not context.is_in_pipeline_scope
    assert context.get_stack_depth() == 0
# endregion pipeline_scope
