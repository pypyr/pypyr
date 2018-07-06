"""types.py unit tests."""
import pypyr.utils.types as types


def test_all_objects_of_type():
    """All of type should be True"""
    assert types.are_all_this_type(int, 1, 2, 3, 4)


def test_none_objects_of_type():
    """None of type should be False"""
    assert not types.are_all_this_type(str, 1, 2, 3, 4)


def test_one_obj_of_type():
    """Only 1 input of type should be True"""
    assert types.are_all_this_type(bool, False)


def test_some_objects_of_type():
    """Odd one out should be False"""
    assert not types.are_all_this_type(str, 1, '2', 3, 4)
