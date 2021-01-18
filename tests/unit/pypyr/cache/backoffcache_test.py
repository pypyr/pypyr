"""backoffcache.py unit tests."""
import pytest
from unittest.mock import patch
from pypyr.errors import PyModuleNotFoundError
import pypyr.cache.backoffcache as backoffcache
import pypyr.retries

# region load_backoff_callable


def test_load_backoff_callable_module_not_found():
    """Module not found raises."""
    with pytest.raises(PyModuleNotFoundError):
        backoffcache.load_backoff_callable('blah-blah-xyz-argh.unlikely-name')


def test_load_backoff_callable_attr_not_found():
    """Attribute not found raises."""
    with pytest.raises(AttributeError) as err:
        backoffcache.load_backoff_callable(
            'tests.arbpack.arbcallables.IDontExist')

    assert str(err.value) == (
        "module 'tests.arbpack.arbcallables' has no attribute 'IDontExist'")


def test_load_backoff_callable_absolute():
    """Load backoff callable with absolute name: package.module.class."""
    f = backoffcache.load_backoff_callable(
        'tests.arbpack.arbcallables.ArbCallable')

    callable_ref = f('ctor in')
    assert callable_ref('arg in 1') == 'from callable: ctor in arg in 1'
    assert callable_ref('arg in 2') == 'from callable: ctor in arg in 2'


def test_load_backoff_callable_bare():
    """Load backoff callable with bare name (no dot)."""
    with pytest.raises(ValueError) as err:
        backoffcache.load_backoff_callable('local_test_arb_callable')

    assert str(err.value) == (
        "Trying to find back-off strategy 'local_test_arb_callable'. If this "
        "is a built-in back-off strategy, are you sure you got the name right?"
        "\nIf you're trying to load a custom callable, name should be in "
        "format 'package.module.ClassName' or 'mod.ClassName'.")

# endregion load_backoff_callable

# region BackoffCache

# region BackoffCache: get_backoff


def test_get_backoff():
    """Backoff callable loads ok."""
    with patch('pypyr.cache.backoffcache.load_backoff_callable') as mock:
        mock.return_value = lambda x: f"{x}test"
        f = backoffcache.BackoffCache().get_backoff("arb")

    mock.assert_called_once_with('arb')
    assert f("arb") == "arbtest"

    # it made a copy
    assert 'arb' not in pypyr.retries.builtin_backoffs


def test_get_backoff_builtin():
    """Load built-in backoff callable."""
    f = backoffcache.BackoffCache().get_backoff('fixed')

    callable_ref = f(sleep=123, max_sleep=456)
    assert callable_ref(789) == 123
    assert callable_ref(999) == 123

# endregion BackoffCache: get_backoff

# region BackoffCache: clear


def test_clear_doesnt_wipe_builtins():
    """Clear shouldn't touch builtins."""
    # Also doesn't touch the og look-up dict.
    bc = backoffcache.BackoffCache()

    og_len = len(bc._cache)
    assert og_len > 1
    assert 'fixed' in bc._cache

    _ = bc.get_backoff('tests.arbpack.arbcallables.ArbCallable')
    assert len(bc._cache) == og_len + 1

    bc.clear()

    # didn't touch the class's built-in dict
    assert len(bc._cache) == og_len
    assert 'fixed' in bc._cache

    # twice in a row to verify clear also makes a copy
    _ = bc.get_backoff('tests.arbpack.arbcallables.ArbCallable')
    assert len(bc._cache) == og_len + 1
    assert len(pypyr.retries.builtin_backoffs) == og_len

    bc.clear()

    # didn't touch the class's built-in dict
    assert len(bc._cache) == og_len
    assert 'fixed' in bc._cache

    # didn't touch the shared built-in dict constant
    assert len(pypyr.retries.builtin_backoffs) == og_len
    assert 'fixed' in pypyr.retries.builtin_backoffs


# endregion BackoffCache: clear

# endregion BackoffCache
