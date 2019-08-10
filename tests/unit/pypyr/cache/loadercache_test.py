"""loadercache.py unit tests."""
import pytest
from unittest.mock import patch
from pypyr.errors import PyModuleNotFoundError
import pypyr.cache.loadercache as loadercache

# ------------------------- load_the_loader --------------------------------#


def test_load_the_loader_module_not_found():
    """Module not found raises."""
    with pytest.raises(PyModuleNotFoundError):
        loadercache.load_the_loader('blah-blah-unlikely-name')


def test_load_the_loader_attr_not_found():
    """Attribute not found raises."""
    with pytest.raises(AttributeError):
        loadercache.load_the_loader(__name__)


def test_load_the_loader_ok():
    """Module with attribute returns function."""
    loadercache.pypeloader_cache.clear()
    f = loadercache.load_the_loader('tests.arbpack.arbloader')
    response = f(pipeline_name='arb', working_dir='/arb')

    assert response == {'pipeline_name': 'arb', 'working_dir': '/arb'}
# ------------------------- END load_the_loader ----------------------------#

# ------------------------- PypeLoaderCache --------------------------------#

# ------------------------- PypeLoaderCache: get_pype_loader ---------------#


def test_get_pype_loader_default():
    """Loader defaults to fileloader."""
    with patch('pypyr.cache.loadercache.load_the_loader') as mock:
        mock.return_value = lambda x: f"{x}test"
        f = loadercache.PypeLoaderCache().get_pype_loader()

    mock.assert_called_once_with('pypyr.pypeloaders.fileloader')
    assert f("arb") == "arbtest"


def test_get_pype_loader_specified():
    """Loader passes loader arg."""
    with patch('pypyr.cache.loadercache.load_the_loader') as mock:
        mock.return_value = lambda x: f"{x}test"
        f = loadercache.PypeLoaderCache().get_pype_loader("arbloader")

    mock.assert_called_once_with('arbloader')
    assert f("arb") == "arbtest"
# ------------------------- PypeLoaderCache: get_pype_loader ---------------#

# ------------------------- END PypeLoaderCache -----------------------------#
