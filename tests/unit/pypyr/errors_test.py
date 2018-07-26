"""errors.py unit tests."""
from pypyr.errors import Error as PypyrError
from pypyr.errors import (
    ContextError,
    KeyInContextHasNoValueError,
    KeyNotInContextError,
    LoopMaxExhaustedError,
    PlugInError,
    PipelineDefinitionError,
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


def test_context_error_raises():
    """ContextError raises with correct message"""
    assert isinstance(ContextError(), PypyrError)

    with pytest.raises(ContextError) as err_info:
        raise ContextError("this is error text right here")

    assert repr(err_info.value) == ("ContextError('this is error "
                                    "text right here',)")


def test_key_not_in_context_error_raises():
    """Key not in context error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(KeyNotInContextError(), PypyrError)
    assert isinstance(KeyNotInContextError(), ContextError)

    with pytest.raises(KeyNotInContextError) as err_info:
        raise KeyNotInContextError("this is error text right here")

    assert repr(err_info.value) == ("KeyNotInContextError('this is error "
                                    "text right here',)")


def test_key_in_context_has_no_value_error_raises():
    """Key not in context value error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(KeyInContextHasNoValueError(), PypyrError)
    assert isinstance(KeyNotInContextError(), ContextError)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        raise KeyInContextHasNoValueError("this is error text right here")

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError('this is error "
        "text right here',)")


def test_loop_max_exhausted_error_raises():
    """LoopMaxExhaustedError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(LoopMaxExhaustedError(), PypyrError)

    with pytest.raises(LoopMaxExhaustedError) as err_info:
        raise LoopMaxExhaustedError("this is error text right here")

    assert repr(err_info.value) == ("LoopMaxExhaustedError('this is error "
                                    "text right here',)")


def test_pipeline_definition_error_raises():
    """PipelineDefinitionError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PipelineDefinitionError(), PypyrError)

    with pytest.raises(PipelineDefinitionError) as err_info:
        raise PipelineDefinitionError("this is error text right here")

    assert repr(err_info.value) == ("PipelineDefinitionError('this is error "
                                    "text right here',)")


def test_pipeline_not_found_error_raises():
    """PipelineNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PipelineNotFoundError(), PypyrError)

    with pytest.raises(PipelineNotFoundError) as err_info:
        raise PipelineNotFoundError("this is error text right here")

    assert repr(err_info.value) == ("PipelineNotFoundError('this is error "
                                    "text right here',)")


def test_plugin_error_raises():
    """Pypyr plugin error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PlugInError(), PypyrError)

    with pytest.raises(PlugInError) as err_info:
        raise PlugInError("this is error text right here")

    assert repr(err_info.value) == ("PlugInError('this is error "
                                    "text right here',)")


def test_pymodule_not_found_error_raises():
    """PyModuleNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PyModuleNotFoundError(), PypyrError)

    with pytest.raises(PyModuleNotFoundError) as err_info:
        raise PyModuleNotFoundError("this is error text right here")

    assert repr(err_info.value) == ("PyModuleNotFoundError('this is error "
                                    "text right here',)")
