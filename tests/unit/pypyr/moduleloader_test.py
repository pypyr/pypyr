"""moduleloader.py unit tests."""
from pypyr.errors import PyModuleNotFoundError
import pypyr.moduleloader
import pytest
import os
import sys


# ------------------------- get_module ---------------------------------------#


def test_get_module_raises():
    """get_module ModuleNotFoundError on module not found."""
    with pytest.raises(PyModuleNotFoundError):
        pypyr.moduleloader.get_module('unlikelyblahmodulenameherexxssz')


def test_get_module_raises_compatible_error():
    """get_module should raise error compatible with ModuleNotFoundError."""
    with pytest.raises(ModuleNotFoundError):
        pypyr.moduleloader.get_module('unlikelyblahmodulenameherexxssz')


def test_get_module_pass():
    """get_module finds a module in cwd"""
    p = os.path.join(
        os.getcwd(),
        'tests',
        'testfiles')
    pypyr.moduleloader.set_working_directory(p)
    arb_module = pypyr.moduleloader.get_module('arb')

    assert arb_module
    assert arb_module.__name__ == 'arb'
    assert hasattr(arb_module, 'arb_attribute')

    sys.path.remove(p)


def test_get_module_in_package_pass():
    """get_module finds a module in a package in cwd using dot notation."""
    p = os.path.join(
        os.getcwd(),
        'tests')
    pypyr.moduleloader.set_working_directory(p)
    arb_module = pypyr.moduleloader.get_module('arbpack.arbmod')

    assert arb_module
    assert arb_module.__name__ == 'arbpack.arbmod'
    assert hasattr(arb_module, 'arbmod_attribute')

    sys.path.remove(p)

# ------------------------- get_module ---------------------------------------#

# ------------------------- set_working_dir ----------------------------------#


def test_set_working_dir():
    """working dir added to sys paths"""
    p = '/arb/path'
    assert p not in sys.path
    pypyr.moduleloader.set_working_directory(p)
    assert p in sys.path
    sys.path.remove(p)

# ------------------------- set_working_dir ----------------------------------#
