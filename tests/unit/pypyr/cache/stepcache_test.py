"""stepcache.py unit tests."""
import pytest
from unittest.mock import patch
from pypyr.errors import PyModuleNotFoundError
import pypyr.cache.stepcache as stepcache

# ------------------------- load_the_step -----------------------------------#


def test_load_the_step_module_not_found():
    """Module not found raises."""
    with pytest.raises(PyModuleNotFoundError):
        stepcache.load_the_step('blah-blah-unlikely-name')


def test_load_the_step_attr_not_found():
    """Attribute not found raises."""
    with pytest.raises(AttributeError):
        stepcache.load_the_step(__name__)


def test_load_the_step_ok():
    """Module with attribute returns function."""
    stepcache.step_cache.clear()
    f = stepcache.load_the_step('tests.arbpack.arbmutatingstep')
    context = {'in': 'inblah'}
    f(context)

    assert context == {'in': 'inblah',
                       'inside_step': 'arb'}
# ------------------------- END load_the_step -------------------------------#

# ------------------------- StepCache ---------------------------------------#

# ------------------------- StepCache: get_step -----------------------------#


def test_get_step():
    """Step loads ok."""
    with patch('pypyr.cache.stepcache.load_the_step') as mock:
        mock.return_value = lambda x: f"{x}test"
        f = stepcache.StepCache().get_step("arbstep")

    mock.assert_called_once_with('arbstep')
    assert f("arb") == "arbtest"
# ------------------------- StepCache: get_step -----------------------------#

# ------------------------- END StepCache -----------------------------------#
