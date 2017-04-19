""""string.py unit tests."""

import pypyr.format.string
import pytest


def test_string_interpolate_works():
    context = {'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}
    input_string = 'Piping {key1} the {key2} wild'
    output = pypyr.format.string.get_interpolated_string(input_string, context)
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_string_interpolate_works_with_no_swaps():
    context = {'key1': 'down', 'key2': 'valleys', 'key3': 'value3'}
    input_string = 'Piping down the valleys wild'
    output = pypyr.format.string.get_interpolated_string(input_string, context)
    assert output == 'Piping down the valleys wild', (
        "string interpolation incorrect")


def test_tag_not_in_context_should_throw():
    """pycode error should raise up to caller."""
    with pytest.raises(KeyError):
        context = {'key1': 'value1'}
        input_string = '{key1} this is {key2} string'
        pypyr.format.string.get_interpolated_string(input_string, context)
