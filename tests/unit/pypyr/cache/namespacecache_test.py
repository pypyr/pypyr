"""namespacecache.py unit tests."""
from sys import intern
from unittest.mock import patch

import pypyr.cache.namespacecache as namespacecache
from pypyr.moduleloader import ImportVisitor

# region parse_and_load


def test_get_namespace_parse_and_load():
    """Parse and load returns namespace dict."""
    source = """\
import math
import tests.arbpack.arbmod
from tests.arbpack import arbmod2
from tests.arbpack import arbmod3 as ab3
from tests.arbpack.arbmultiattr import arb_attr as x, arb_func as y
"""
    out = namespacecache.NamespaceCache().get_namespace(source)

    assert len(out) == 6
    assert all(key in out for key in ['math', 'tests', 'arbmod2', 'ab3',
                                      'x', 'y'])


# endregion parse_and_load

# region NamespaceCache

# region NamespaceCache: get_namespace


def test_get_namespace_cache_hit():
    """Get namespace interns and hits cache."""
    with patch.object(ImportVisitor,
                      'get_namespace',
                      return_value='ns') as mock:
        ns = namespacecache.NamespaceCache().get_namespace("arbkey")

    mock.assert_called_once_with('arbkey')
    assert ns == "ns"


def test_get_namespace_same_obj():
    """Get namespace returns same obj for same source."""
    source = "from tests.arbpack import arbmod3 as ab3"
    cache = namespacecache.NamespaceCache()
    ns = cache.get_namespace(source)
    assert len(ns) == 1
    assert ns['ab3'].arb_func_in_arbmod3(321) == 321

    ns2 = cache.get_namespace("from tests.arbpack import arbmod3 as ab3")
    assert ns2 is ns
    assert len(ns) == 1
    assert ns['ab3'].arb_func_in_arbmod3(321) == 321

    intern("from tests.arbpack import arbmod3 as ab3") is list(
        cache._cache.keys())[0]

# endregion NamespaceCache: get_namespace

# endregion NamespaceCache
