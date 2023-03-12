"""pypyr/cache/admin.py unit tests."""
import pypyr.cache.admin as cache_admin

from pypyr.cache.backoffcache import backoff_cache
from pypyr.cache.filecache import file_cache
from pypyr.cache.loadercache import loader_cache
from pypyr.cache.namespacecache import pystring_namespace_cache
from pypyr.cache.parsercache import contextparser_cache
from pypyr.cache.stepcache import step_cache
from pypyr.retries import builtin_backoffs

# region load_backoff_callable


def test_cache_clear_all():
    """Clear all cache."""
    cache_admin.clear_all()

    assert backoff_cache._cache == builtin_backoffs
    assert file_cache._cache == {}
    assert loader_cache._cache == {}
    assert pystring_namespace_cache._cache == {}
    assert contextparser_cache._cache == {}
    assert step_cache._cache == {}

    backoff_cache.get_backoff('tests.arbpack.arbcallables.ArbCallable')
    assert len(backoff_cache._cache) == len(builtin_backoffs) + 1

    # testing full file cache clear in pypyr/loaders/file_test.py in:
    # test_get_pipeline_definition_clear_all_cache
    file_cache._cache['arb'] = 'delete me'
    assert len(file_cache._cache) == 1

    loader_cache.get_pype_loader('tests.arbpack.arbloader')
    assert len(loader_cache._cache) == 1

    pystring_namespace_cache.get_namespace('import math')
    assert len(pystring_namespace_cache._cache) == 1

    contextparser_cache.get_context_parser('tests.arbpack.arbparser')
    assert len(contextparser_cache._cache) == 1

    step_cache.get_step('tests.arbpack.arbmutatingstep')
    assert len(step_cache._cache) == 1

    cache_admin.clear_all()

    assert backoff_cache._cache == builtin_backoffs
    assert file_cache._cache == {}
    assert loader_cache._cache == {}
    assert pystring_namespace_cache._cache == {}
    assert contextparser_cache._cache == {}
    assert step_cache._cache == {}
