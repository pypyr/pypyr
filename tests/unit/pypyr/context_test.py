"""context.py unit tests."""
from collections.abc import MutableMapping
from pypyr.context import Context
import pytest

# ------------------- behaves like a dictionary-------------------------------#


def test_context_is_dictionary_like():
    """Context should behave like a dictionary"""
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

# ------------------- behaves like a dictionary-------------------------------#

# ------------------- asserts ------------------------------------------------#


def test_assert_key_has_value_fails_on_context_empty():
    """Expect AssertionError if context empty."""
    context = Context()
    with pytest.raises(AssertionError):
        context.assert_key_has_value('key', 'desc')


def test_assert_key_has_value_fails_on_key_none():
    """Expect AssertionError if assert key is None."""
    context = Context({'key1': 'value1'})
    with pytest.raises(AssertionError):
        context.assert_key_has_value(None, None)


def test_assert_key_has_value_fails_key_not_found():
    """AssertionError if context doesn't have key on assert."""
    context = Context({'key1': 'value1'})
    with pytest.raises(AssertionError):
        context.assert_key_has_value('notindict', None)


def test_assert_key_has_value_fails_key_error_message():
    """AssertionError if context missing key and assert message correct."""
    context = Context({'key1': 'value1'})
    with pytest.raises(AssertionError) as err_info:
        context.assert_key_has_value('notindict', 'mydesc')

    assert repr(err_info.value) == ("AssertionError(\"context['notindict'] "
                                    "doesn't exist. It must have a value for "
                                    "mydesc.\",)")


def test_assert_key_has_value_fails_key_empty():
    """AssertionError if context dictionary key value is None."""
    context = Context({'key1': None})
    with pytest.raises(AssertionError):
        context.assert_key_has_value('key1', None)


def test_assert_key_has_value_passes():
    """Pass if key_in_dict_has_value dictionary key has value."""
    context = Context({'key1': 'value1'})
    context.assert_key_has_value('key1', None)


def test_assert_keys_have_values_passes():
    """Pass if list of keys all found in context dictionary."""
    context = Context({'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})
    context.assert_keys_have_values(None, 'key1', 'key3')


def test_assert_keys_have_values_fails():
    """AssertionError if list of keys not all found in context."""
    with pytest.raises(AssertionError):
        context = Context({'key1': 'value1',
                           'key2': 'value2',
                           'key3': 'value3'})
        context.assert_keys_have_values(None,
                                        'key1',
                                        'key4',
                                        'key2',
                                        )

# ------------------- asserts ------------------------------------------------#

# ------------------- formats ------------------------------------------------#


def test_string_interpolate_works():
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping {key1} the {key2} wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_works_with_no_swaps():
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping down the valleys wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_escapes_double_curly():
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping {{ down the valleys wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping { down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_escapes_double_curly_pair():
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    context['input_string'] = 'Piping {{down}} the valleys wild'
    output = context.get_formatted('input_string')
    assert output == 'Piping {down} the valleys wild', (
        "string interpolation incorrect")


def test_single_curly_should_throw():
    with pytest.raises(ValueError):
        context = Context({'key1': 'value1'})
        context['input_string'] = '{key1} this { is {key2} string'
        context.get_formatted('input_string')


def test_tag_not_in_context_should_throw():
    with pytest.raises(KeyError):
        context = Context({'key1': 'value1'})
        context['input_string'] = '{key1} this is {key2} string'
        context.get_formatted('input_string')


def test_context_item_not_a_string_should_throw():
    with pytest.raises(TypeError):
        context = Context({'key1': 'value1'})
        context['input_string'] = 77
        context.get_formatted('input_string')


def test_input_string_interpolate_works():
    context = Context({'key1': 'down', 'key2': 'valleys', 'key3': 'value3'})
    input_string = 'Piping {key1} the {key2} wild'
    output = context.get_formatted_string(input_string)
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_input_string_tag_not_in_context_should_throw():
    with pytest.raises(KeyError):
        context = Context({'key1': 'value1'})
        input_string = '{key1} this is {key2} string'
        context.get_formatted_string(input_string)


def test_input_string_not_a_string_throw():
    with pytest.raises(TypeError):
        context = Context({'key1': 'value1'})
        input_string = 77
        context.get_formatted_string(input_string)
# ------------------- formats ------------------------------------------------#

# ------------------- key info -----------------------------------------------#


def test_key_in_context():
    context = Context({'k1': 'v1', 'k2': False, 'k3': ['one', 'two']})

    k1, = context.keys_exist('k1')
    assert k1
    k1, k2, k3 = context.keys_exist('k1', 'k2', 'k3')
    assert k1 and k2 and k3

    k4, k2, k1 = context.keys_exist('k4', 'k2', 'k1')
    assert k1 and k2 and not k4


def test_keys_of_type_exist_single():
    """return a single tuple"""
    context = Context({'k1': 'v1', 'k2': False, 'k3': ['one', 'two']})

    k1, = context.keys_of_type_exist(('k1', str),)
    assert k1
    assert k1.key == 'k1'
    assert k1.key_in_context
    assert k1.expected_type is str
    assert k1.is_expected_type


def test_keys_of_type_exist_triple():
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

    assert k2
    assert k2.key == 'k2'
    assert k2.key_in_context
    assert k2.expected_type is list
    assert not k2.is_expected_type

    assert k3
    assert k3.key == 'k3'
    assert k3.key_in_context
    assert k3.expected_type is list
    assert k3.is_expected_type


def test_keys_none_exist():
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

    assert k5
    assert k5.key == 'k5'
    assert not k5.key_in_context
    assert k5.expected_type is bool
    assert k4.is_expected_type is None

    assert k6
    assert k6.key == 'k6'
    assert not k6.key_in_context
    assert k6.expected_type is list
    assert k6.is_expected_type is None


# ------------------- key info -----------------------------------------------#
