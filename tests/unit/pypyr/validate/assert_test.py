"""assert.py unit tests."""
import pypyr.validate.asserts
import pytest
import pypyr.version


def test_key_in_context_has_value_fails_on_context_none():
    """Expect AssertionError if key_in_dict_has_value dictionary is None."""
    with pytest.raises(AssertionError):
        pypyr.validate.asserts.key_in_context_has_value(None, 'key', 'desc')


def test_key_in_context_has_value_fails_on_context_empty():
    """Expect AssertionError if key_in_dict_has_value dictionary is None."""
    with pytest.raises(AssertionError):
        pypyr.validate.asserts.key_in_context_has_value({}, 'key', 'desc')


def test_key_in_context_has_value_fails_on_key_none():
    """Expect AssertionError if key_in_dict_has_value key is None."""
    with pytest.raises(AssertionError):
        pypyr.validate.asserts.key_in_context_has_value({'key1': 'value1'},
                                                        None,
                                                        None)


def test_key_in_context_has_value_fails_key_not_found():
    """AssertionError if key_in_dict_has_value dictionary doesn't have key."""
    with pytest.raises(AssertionError):
        pypyr.validate.asserts.key_in_context_has_value({'key1': 'value1'},
                                                        'notindict',
                                                        None)


def test_key_in_context_has_value_fails_key_empty():
    """AssertionError if key_in_dict_has_value dictionary key value is None."""
    with pytest.raises(AssertionError):
        pypyr.validate.asserts.key_in_context_has_value({'key1': None},
                                                        'key1',
                                                        None)


def test_key_in_context_has_value_passes():
    """Pass if key_in_dict_has_value dictionary key has value."""
    pypyr.validate.asserts.key_in_context_has_value({'key1': 'value1'},
                                                    'key1',
                                                    None)


def test_keys_in_context_has_value_passes():
    """Pass if list of keys all found in context dictionary."""
    context = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
    pypyr.validate.asserts.keys_in_context_has_value(context,
                                                     ['key1', 'key3'],
                                                     None)


def test_keys_in_context_not_found():
    """AssertionError if list of keys not all found in context."""
    with pytest.raises(AssertionError):
        context = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        pypyr.validate.asserts.keys_in_context_has_value(context,
                                                         ['key1',
                                                          'key4',
                                                          'key2'],
                                                         None)
