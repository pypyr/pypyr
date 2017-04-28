"""errors.py unit tests."""
from pypyr.errors import Error as PypyrError
from pypyr.errors import (PlugInError,
                          PipelineNotFoundError,
                          PyModuleNotFoundError)
import pytest


def test_base_error_raises():
    """Pypyr root Error raises with correct message."""
    assert isinstance(PypyrError(), Exception)

    with pytest.raises(PypyrError) as err_info:
        raise PypyrError("this is error text right here")

    assert repr(err_info.value) == ("Error('this is error text "
                                    "right here',)")


def test_plugin_error_raises():
    """Pypyr plugin error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PlugInError(), PypyrError)

    with pytest.raises(PlugInError) as err_info:
        raise PlugInError("this is error text right here")

    assert repr(err_info.value) == ("PlugInError('this is error "
                                    "text right here',)")


def test_pipeline_not_found_error_raises():
    """PipelineNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PipelineNotFoundError(), PypyrError)

    with pytest.raises(PipelineNotFoundError) as err_info:
        raise PipelineNotFoundError("this is error text right here")

    assert repr(err_info.value) == ("PipelineNotFoundError('this is error "
                                    "text right here',)")


def test_pymodule_not_found_error_raises():
    """PyModuleNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PyModuleNotFoundError(), PypyrError)

    with pytest.raises(PyModuleNotFoundError) as err_info:
        raise PyModuleNotFoundError("this is error text right here")

    assert repr(err_info.value) == ("PyModuleNotFoundError('this is error "
                                    "text right here',)")
