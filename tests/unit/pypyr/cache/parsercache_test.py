"""parsercache.py unit tests."""
import pytest
from unittest.mock import patch
from pypyr.errors import PyModuleNotFoundError
import pypyr.cache.parsercache as parsercache

# ------------------------- load_the_parser --------------------------------#


def test_load_the_parser_module_not_found():
    """Module not found raises."""
    with pytest.raises(PyModuleNotFoundError):
        parsercache.load_the_parser('blah-blah-unlikely-name')


def test_load_the_parser_attr_not_found():
    """Attribute not found raises."""
    with pytest.raises(AttributeError):
        parsercache.load_the_parser(__name__)


def test_load_the_parser_ok():
    """Module with attribute returns function."""
    parsercache.contextparser_cache.clear()
    f = parsercache.load_the_parser('tests.arbpack.arbparser')
    response = f(context_arg='blah')

    assert response == {'parsed_context': 'blah'}
# ------------------------- END load_the_parser ----------------------------#

# ------------------------- ContextParserCache -----------------------------#

# ------------------------- ContextParserCache: get_context_parser ---------#


def test_get_pype_loader_specified():
    """Loader passes loader arg."""
    with patch('pypyr.cache.parsercache.load_the_parser') as mock:
        mock.return_value = lambda x: f"{x}test"
        f = parsercache.ContextParserCache().get_context_parser("arbparser")

    mock.assert_called_once_with('arbparser')
    assert f("arb") == "arbtest"
# ------------------------- ContextParserCache: get_context_parser ---------#

# ------------------------- END ContextParserCache --------------------------#
