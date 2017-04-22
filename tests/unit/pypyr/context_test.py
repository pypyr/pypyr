"""context.py unit tests."""
from pypyr.context import Context
import pytest

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
    context.asserts_keys_have_values(['key1', 'key3'], None)


def test_assert_keys_have_values_fails():
    """AssertionError if list of keys not all found in context."""
    with pytest.raises(AssertionError):
        context = Context({'key1': 'value1',
                           'key2': 'value2',
                           'key3': 'value3'})
        context.asserts_keys_have_values(['key1',
                                          'key4',
                                          'key2'],
                                         None)

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
    """pycode error should raise up to caller."""
    with pytest.raises(ValueError):
        context = Context({'key1': 'value1'})
        context['input_string'] = '{key1} this { is {key2} string'
        context.get_formatted('input_string')


def test_tag_not_in_context_should_throw():
    """pycode error should raise up to caller."""
    with pytest.raises(KeyError):
        context = Context({'key1': 'value1'})
        context['input_string'] = '{key1} this is {key2} string'
        context.get_formatted('input_string')

# ------------------- formats ------------------------------------------------#
