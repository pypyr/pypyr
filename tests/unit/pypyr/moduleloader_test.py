"""moduleloader.py unit tests."""
from pypyr.errors import (PipelineNotFoundError,
                          PyModuleNotFoundError)
import pypyr.moduleloader
import pytest
import os
import sys


# ------------------------- get_module ---------------------------------------#


def test_get_module_raises():
    """get_module ModuleNotFoundError on module not found."""
    with pytest.raises(PyModuleNotFoundError):
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

# ------------------------- get_pipeline_path --------------------------------#


def test_get_pipeline_path_in_working_dir():
    """Find a pipeline in the working dir"""
    working_dir = os.path.join(
        os.getcwd(),
        'tests')
    path_found = pypyr.moduleloader.get_pipeline_path('testpipeline',
                                                      working_dir)

    expected_path = os.path.join(
        os.getcwd(),
        'tests',
        'pipelines',
        'testpipeline.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_in_pypyr_dir():
    """Find a pipeline in the pypyr install dir"""
    working_dir = os.path.join(
        os.getcwd(),
        'tests')
    path_found = pypyr.moduleloader.get_pipeline_path('donothing',
                                                      working_dir)

    expected_path = os.path.join(
        os.getcwd(),
        'pypyr',
        'pipelines',
        'donothing.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_raises():
    """Failure to find pipeline should raise PipelineNotFoundError"""
    with pytest.raises(PipelineNotFoundError) as err:
        pypyr.moduleloader.get_pipeline_path('unlikelypipeherexyz',
                                             os.getcwd())

    current_path = os.path.join(
        os.getcwd(),
        'pipelines')

    pypyr_path = os.path.join(
        os.getcwd(),
        'pypyr',
        'pipelines')

    expected_msg = (f'unlikelypipeherexyz.yaml not found in either '
                    f'{current_path} or {pypyr_path}')

    assert repr(err.value) == f'PipelineNotFoundError(\'{expected_msg}\',)'


# ------------------------- get_pipeline_path --------------------------------#
#
# ------------------------- set_working_dir ----------------------------------#


def test_set_working_dir():
    """working dir added to sys paths"""
    p = '/arb/path'
    assert p not in sys.path
    pypyr.moduleloader.set_working_directory(p)
    assert p in sys.path
    sys.path.remove(p)

# ------------------------- set_working_dir ----------------------------------#
