"""cache.py unit tests."""
import logging
from unittest.mock import call, MagicMock
from pypyr.cache.cache import Cache
from tests.common.utils import patch_logger


def test_cache_get_miss():
    """Cache get should execute creator."""
    cache = Cache()
    creator_mock = MagicMock()
    creator_mock.return_value = "created obj"

    with patch_logger('pypyr.cache', logging.DEBUG) as mock_logger_debug:
        obj = cache.get('one', lambda: creator_mock("1"))

    assert obj == "created obj"
    creator_mock.assert_called_once_with("1")
    mock_logger_debug.assert_called_once_with(
        "one not found in cache. . . creating")


def test_cache_get_hit():
    """Cache get where found in cache shouldn't execute creator."""
    cache = Cache()
    creator_mock = MagicMock()
    creator_mock.side_effect = ["created obj1", "created obj2", "created obj3"]

    with patch_logger('pypyr.cache', logging.DEBUG) as mock_logger_debug:
        obj1 = cache.get('one', lambda: creator_mock("1"))
        obj2 = cache.get('one', lambda: creator_mock("2"))
        obj3 = cache.get('one', lambda: creator_mock("3"))

    assert obj1 == "created obj1"
    assert obj2 == "created obj1"
    assert obj3 == "created obj1"

    creator_mock.assert_called_once_with("1")
    assert mock_logger_debug.mock_calls == [
        call("one not found in cache. . . creating"),
        call("one loading from cache"),
        call("one loading from cache")]

    obj4 = creator_mock("4")
    assert obj4 == "created obj2"


def test_cache_multiple_items_get_hit_closures():
    """Cache with multiple items work."""
    cache = Cache()

    def closure(x, y):
        def inner():
            return x + y
        return inner

    with patch_logger('pypyr.cache', logging.DEBUG) as mock_logger_debug:
        obj1 = cache.get('one', closure(2, 3))
        obj2 = cache.get('two', closure(4, 5))
        obj3 = cache.get('three', closure(6, 7))
        obj4 = cache.get('one', closure(8, 9))

    assert obj1 == 5
    assert obj2 == 9
    assert obj3 == 13
    assert obj4 == 5

    assert mock_logger_debug.mock_calls == [
        call("one not found in cache. . . creating"),
        call("two not found in cache. . . creating"),
        call("three not found in cache. . . creating"),
        call("one loading from cache")]


def test_cache_clear():
    """Cache should clear on clear()."""
    cache = Cache()

    def closure(x, y):
        def inner():
            return x + y
        return inner

    with patch_logger('pypyr.cache', logging.DEBUG) as mock_logger_debug:
        obj1 = cache.get('one', closure(2, 3))
        obj2 = cache.get('two', closure(4, 5))
        obj3 = cache.get('one', closure(6, 7))

    cache.clear()
    assert len(cache._cache) == 0
    assert obj1 == 5
    assert obj2 == 9
    assert obj3 == 5

    assert mock_logger_debug.mock_calls == [
        call("one not found in cache. . . creating"),
        call("two not found in cache. . . creating"),
        call("one loading from cache")]

    obj1 = cache.get('one', closure(2, 3))
    obj2 = cache.get('two', closure(4, 5))
    obj3 = cache.get('one', closure(6, 7))

    assert len(cache._cache) == 2
    assert obj1 == 5
    assert obj2 == 9
    assert obj3 == 5
