"""Arbitrary module with a test attribute.

DON'T use me anywhere except moduleloader_test.py > test_import_visitor.

Because otherwise coverage will drop <100% since Python import machinery will
cache the module lookup and test_import_visitor explicitly tests a code-path
where a module is not found in cache.

Believe it or not, this is the least painful way of achieving it.
"""


def arb_func_in_arbmod4(arg):
    """Arbitrary function just returns input."""
    return arg
