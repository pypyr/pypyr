"""asserts.py unit tests."""
import pytest
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          KeyInContextHasNoValueError)
from pypyr.utils import asserts

# region assert_key_exists


def test_assert_key_exists_none():
    """Key value is None."""
    asserts.assert_key_exists({None: 'b'}, None, 'caller')

    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_exists({'a': 'b'}, None, 'caller')

    assert str(err.value) == (
        "context[None] doesn't exist. It must exist for caller.")


def test_assert_key_exists_int():
    """Key value is an int."""
    asserts.assert_key_exists({1: 'b'}, 1, 'caller')

    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_exists({'a': 'b'}, 1, 'caller')

    assert str(err.value) == (
        "context[1] doesn't exist. It must exist for caller.")


def test_assert_key_exists_with_parent():
    """Parent gives correct error message."""
    asserts.assert_key_exists({'a': 'b'}, 'a', 'caller', 'parent')

    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_exists({'a': 'b'}, 'key', 'caller', 'parent')

    assert str(err.value) == (
        "context['parent']['key'] doesn't exist. It must exist for caller.")


def test_assert_key_has_value_object_not_iterable():
    """Object is None should raise."""
    with pytest.raises(ContextError) as err:
        asserts.assert_key_has_value(obj=1,
                                     key=2,
                                     caller='arb caller',
                                     parent=3)

    assert str(err.value) == (
        "context[3] must exist, be iterable and contain 2 for "
        "arb caller. argument of type 'int' is not iterable")


def test_assert_key_has_value_object_not_iterable_no_parent():
    """Object is None should raise with no parent."""
    with pytest.raises(ContextError) as err:
        asserts.assert_key_has_value(obj=1,
                                     key=2,
                                     caller='arb caller')

    assert str(err.value) == (
        "context[2] must exist and be iterable for arb caller. argument of "
        "type 'int' is not iterable")

# endregion assert_key_exists

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

# region assert_key_is_truthy


def test_assert_key_is_truthy_passes():
    """Success case."""
    asserts.assert_key_is_truthy(obj={'k1': 'v1'},
                                 key='k1',
                                 caller='arb caller',
                                 parent='parent name')


def test_assert_key_is_truthy_value_empty():
    """Is a truthy."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_key_is_truthy(obj={'k1': ''},
                                     key='k1',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == ("context['parent name']['k1'] must have a value "
                              "for arb caller.")


def test_assert_key_is_truthy_none():
    """Key value is none."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_key_is_truthy(obj={'k1': None},
                                     key='k1',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == ("context['parent name']['k1'] must have a value "
                              "for arb caller.")


def test_assert_key_is_truthy_none_no_parent():
    """Key value is none and no parent."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_key_is_truthy(obj={'k1': None},
                                     key='k1',
                                     caller='arb caller')

    assert str(err.value) == "context['k1'] must have a value for arb caller."


def test_assert_key_is_truthy_key_not_there():
    """Key not in object."""
    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_is_truthy(obj={'k1': None},
                                     key='k2',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == ("context['parent name']['k2'] doesn't exist. "
                              "It must exist for arb caller.")


def test_assert_key_is_truthy_key_not_there_no_parent():
    """Key not in object and no parent."""
    with pytest.raises(KeyNotInContextError) as err:
        asserts.assert_key_is_truthy(obj={'k1': None},
                                     key='k2',
                                     caller='arb caller')

    assert str(err.value) == ("context['k2'] doesn't exist. "
                              "It must exist for arb caller.")


def test_assert_key_is_truthy_object_none():
    """Object is None should raise."""
    with pytest.raises(ContextError) as err:
        asserts.assert_key_is_truthy(obj=None,
                                     key='k1',
                                     caller='arb caller',
                                     parent='parent name')

    assert str(err.value) == (
        "context['parent name'] must exist, be iterable and contain 'k1' for "
        "arb caller. argument of type 'NoneType' is not iterable")


def test_assert_key_is_truthy_object_none_no_parent():
    """Object is None should raise with no parent."""
    with pytest.raises(ContextError) as err:
        asserts.assert_key_is_truthy(obj=None,
                                     key='k1',
                                     caller='arb caller')

    assert str(err.value) == (
        "context['k1'] must exist and be iterable for arb caller. argument of "
        "type 'NoneType' is not iterable")
# endregion assert_key_is_truthy

# region assert_keys_are_truthy


def test_assert_keys_are_truthy():
    """Multiple keys on truthy check."""
    asserts.assert_keys_are_truthy(obj={'k1': 'v1', 'k2': 'v2', 'k3': 'v3'},
                                   keys=('k1', 'k3'),
                                   caller='arb caller',
                                   parent='parent name')


def test_assert_keys_are_truthy_none():
    """Key value is none for one of the keys raise error."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_keys_are_truthy(obj={'k1': 'v1',
                                            'k2': None,
                                            'k3': 'v3'},
                                       keys=['k1', 'k3', 'k2'],
                                       caller='arb caller',
                                       parent='parent name')

    assert str(err.value) == ("context['parent name']['k2'] must have a value "
                              "for arb caller.")


def test_assert_keys_are_truthy_empty():
    """Key value is empty for one of the keys raise error."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        asserts.assert_keys_are_truthy(obj={'k1': 'v1',
                                            'k2': '',
                                            'k3': 'v3'},
                                       keys=['k1', 'k3', 'k2'],
                                       caller='arb caller',
                                       parent='parent name')

    assert str(err.value) == ("context['parent name']['k2'] must have a value "
                              "for arb caller.")
# endregion assert_keys_are_truthy
