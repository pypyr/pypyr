"""moduleloader.py unit tests."""
from pathlib import Path
import pytest
import sys
from pypyr.errors import PyModuleNotFoundError
import pypyr.moduleloader


# ------------------------- get_module ---------------------------------------#


def test_get_module_raises():
    """On get_module ModuleNotFoundError on module not found."""
    with pytest.raises(PyModuleNotFoundError) as err:
        pypyr.moduleloader.get_module('unlikelyblahmodulenameherexxssz')

    assert str(err.value) == (
        "unlikelyblahmodulenameherexxssz.py should be in your working "
        "dir or it should be installed to the python path."
        "\nIf you have 'package.sub.mod' your current working "
        "dir should contain ./package/sub/mod.py\n"
        "If you specified 'mymodulename', your current "
        "working dir should contain ./mymodulename.py\n"
        "If the module is not in your current working dir, it "
        "must exist in your current python path - so you "
        "should have run pip install or setup.py")


def test_get_module_raises_compatible_error():
    """get_module should raise error compatible with ModuleNotFoundError."""
    with pytest.raises(ModuleNotFoundError):
        pypyr.moduleloader.get_module('unlikelyblahmodulenameherexxssz')


def test_get_module_raises_friendly_on_package_import():
    """get_module should not obscure missing module in existing package."""
    p = Path.cwd().joinpath('tests')
    pypyr.moduleloader.set_working_directory(p)

    with pytest.raises(PyModuleNotFoundError) as err:
        pypyr.moduleloader.get_module('arbpack.idontexist')

    assert str(err.value) == (
        "arbpack.idontexist.py should be in your working "
        "dir or it should be installed to the python path."
        "\nIf you have 'package.sub.mod' your current working "
        "dir should contain ./package/sub/mod.py\n"
        "If you specified 'mymodulename', your current "
        "working dir should contain ./mymodulename.py\n"
        "If the module is not in your current working dir, it "
        "must exist in your current python path - so you "
        "should have run pip install or setup.py")

    sys.path.remove(str(p))


def test_get_module_raises_on_inner_import():
    """get_module should not hide failing import statements in imported mod."""
    p = Path.cwd().joinpath('tests')
    pypyr.moduleloader.set_working_directory(p)

    with pytest.raises(PyModuleNotFoundError) as err:
        pypyr.moduleloader.get_module('arbpack.arbinvalidimportmod')

    assert str(err.value) == (
        'error importing module blahblah in arbpack.arbinvalidimportmod')

    sys.path.remove(str(p))


def test_get_module_pass():
    """Pass when get_module finds a module in cwd."""
    p = Path.cwd().joinpath('tests', 'testfiles')
    pypyr.moduleloader.set_working_directory(p)

    arb_module = pypyr.moduleloader.get_module('arb')

    assert arb_module
    assert arb_module.__name__ == 'arb'
    assert hasattr(arb_module, 'arb_attribute')

    sys.path.remove(str(p))


def test_get_module_in_package_pass():
    """See get_module find a module in a package in cwd using dot notation."""
    p = Path.cwd().joinpath('tests')
    pypyr.moduleloader.set_working_directory(p)
    arb_module = pypyr.moduleloader.get_module('arbpack.arbmod')

    assert arb_module
    assert arb_module.__name__ == 'arbpack.arbmod'
    assert hasattr(arb_module, 'arbmod_attribute')

    sys.path.remove(str(p))

# ------------------------- get_module ---------------------------------------#

# region WorkingDir


def test_working_dir_set_default():
    """Set working dir to cwd if None."""
    w = pypyr.moduleloader.WorkingDir()
    w.set_working_directory(None)
    assert w.get_working_directory() == Path.cwd()


def test_working_dir_get_before_set():
    """Get working dir before set raises."""
    with pytest.raises(ValueError) as err:
        w = pypyr.moduleloader.WorkingDir()
        w.get_working_directory()

    assert str(err.value) == 'working directory not set.'


def test_set_working_dir():
    """Working dir added to sys paths."""
    p = '/arb/path'
    assert p not in sys.path
    pypyr.moduleloader.set_working_directory(p)
    assert p in sys.path
    sys.path.remove(p)

# endregion WorkingDir
