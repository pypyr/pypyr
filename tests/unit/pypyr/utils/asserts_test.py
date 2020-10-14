"""asserts.py unit tests."""
import pytest
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          KeyInContextHasNoValueError)
from pypyr.utils import asserts

# region assert_key_has_value


def test_assert_key_has_value_passes():
    """Success case."""
    asserts.assert_key_has_value(obj={'k1': 'v1'},
                                 key='k1',
                                 caller='arb caller',
                                 parent='parent name')


def test_assert_key_value_empty():
    """Not a truthy."""
    asserts.assert_key_has_value(obj={'k1': ''},
                                 key='k1',
                                 caller='arb caller',
                                 parent='parent name')


def test_assert_key_has_value_none():
    """Key value is none."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_key_has_value(obj={'k1': None},
                                     key='k1',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == ("context['parent name']['k1'] must have a value "
                              "for arb caller.")


def test_assert_key_has_value_none_no_parent():
    """Key value is none and no parent."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_key_has_value(obj={'k1': None},
                                     key='k1',
                                     caller='arb caller')

    assert str(err.value) == "context['k1'] must have a value for arb caller."


def test_assert_key_has_value_key_not_there():
    """Key not in object."""
    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_has_value(obj={'k1': None},
                                     key='k2',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == ("context['parent name']['k2'] doesn't exist. "
                              "It must exist for arb caller.")


def test_assert_key_has_value_key_not_there_no_parent():
    """Key not in object and no parent."""
    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_has_value(obj={'k1': None},
                                     key='k2',
                                     caller='arb caller')

    assert str(err.value) == ("context['k2'] doesn't exist. "
                              "It must exist for arb caller.")


def test_assert_key_has_value_object_none():
    """Object is None should raise."""
    with pytest.raises(ContextError) as err:
        asserts.assert_key_has_value(obj=None,
                                     key='k1',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == (
        "context['parent name'] must exist, be iterable and contain 'k1' for "
        "arb caller. argument of type 'NoneType' is not iterable")


def test_assert_key_has_value_object_none_no_parent():
    """Object is None should raise with no parent."""
    with pytest.raises(ContextError) as err:
        asserts.assert_key_has_value(obj=None,
                                     key='k1',
                                     caller='arb caller')

    assert str(err.value) == (
        "context['k1'] must exist and be iterable for arb caller. argument of "
        "type 'NoneType' is not iterable")
# endregion assert_key_has_value
