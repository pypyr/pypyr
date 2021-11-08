"""types.py unit tests."""
import pypyr.utils.types as types

# region are_all_this_type


def test_all_objects_of_type():
    """All of type should be True."""
    assert types.are_all_this_type(int, 1, 2, 3, 4)


def test_none_objects_of_type():
    """None of type should be False."""
    assert not types.are_all_this_type(str, 1, 2, 3, 4)


def test_one_obj_of_type():
    """Only 1 input of type should be True."""
    assert types.are_all_this_type(bool, False)


def test_some_objects_of_type():
    """Odd one out should be False."""
    assert not types.are_all_this_type(str, 1, '2', 3, 4)

# endregion are_all_this_type

# region cast_to_bool


def test_cast_to_bool():
    """Special strings eval true."""
    assert types.cast_to_bool('TRUE') is True
    assert types.cast_to_bool('true') is True
    assert types.cast_to_bool(1) is True
    assert types.cast_to_bool(1.0) is True
    assert types.cast_to_bool(2) is True

    assert types.cast_to_bool(0) is False
    assert types.cast_to_bool('FALSE') is False
    assert types.cast_to_bool('arb') is False
    assert types.cast_to_bool(None) is False
# endregion cast_to_bool

# region cast_to_type


def test_cast_to_type_with_conversion():
    """In obj casts to out type."""
    out = types.cast_to_type(12, str)
    assert isinstance(out, str)
    assert out == "12"


def test_cast_to_type_not_needed():
    """In obj is already out type, no conversion needed."""
    out = types.cast_to_type(12, int)
    assert isinstance(out, int)
    assert out == 12


def test_cast_to_type_str_to_bool():
    """String to bool always true."""
    out = types.cast_to_type('False', bool)
    assert isinstance(out, bool)
    assert out
# endregion cast_to_type

# region empty_if_none


def test_empty_if_none():
    """Empty if none returns empty string when None."""
    assert types.empty_if_none(None) == ''
    assert types.empty_if_none('') == ''
    assert types.empty_if_none('arb') == 'arb'
    assert types.empty_if_none(True) is True
    v = ValueError()
    assert types.empty_if_none(v) == v
# endregion empty_if_none
