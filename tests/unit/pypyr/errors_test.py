"""errors.py unit tests."""
from pypyr.errors import Error as PypyrError
from pypyr.errors import (
    ContextError,
    get_error_name,
    HandledError,
    KeyInContextHasNoValueError,
    KeyNotInContextError,
    LoopMaxExhaustedError,
    PlugInError,
    PipelineDefinitionError,
    PipelineNotFoundError,
    PyModuleNotFoundError,
    Stop,
    StopStepGroup,
    StopPipeline,
    ControlOfFlowInstruction,
    Call,
    Jump)
import pytest


def test_get_error_name_builtin():
    """Builtin returns bare name on get_error_name."""
    assert get_error_name(ValueError('blah')) == 'ValueError'


def test_get_error_name_canonical():
    """Other error returns modulename.name on get_error_name."""
    assert get_error_name(ContextError('blah')) == 'pypyr.errors.ContextError'


def test_base_error_raises():
    """Pypyr root Error raises with correct message."""
    assert isinstance(PypyrError(), Exception)

    with pytest.raises(PypyrError) as err_info:
        raise PypyrError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_context_error_raises():
    """ContextError raises with correct message"""
    assert isinstance(ContextError(), PypyrError)

    with pytest.raises(ContextError) as err_info:
        raise ContextError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_handled_error_raises():
    """HandledError raises with correct message and with from."""
    assert isinstance(HandledError(), PypyrError)

    try:
        try:
            raise ContextError("this is error text right here")
        except ContextError as e:
            raise HandledError("handled") from e
    except Exception as err_info:
        assert str(err_info) == "handled"
        inner = err_info.__cause__
        assert isinstance(inner, ContextError)
        assert str(inner) == "this is error text right here"


def test_key_not_in_context_error_raises():
    """Key not in context error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(KeyNotInContextError(), PypyrError)
    assert isinstance(KeyNotInContextError(), ContextError)

    with pytest.raises(KeyNotInContextError) as err_info:
        raise KeyNotInContextError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_key_in_context_has_no_value_error_raises():
    """Key not in context value error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(KeyInContextHasNoValueError(), PypyrError)
    assert isinstance(KeyNotInContextError(), ContextError)

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        raise KeyInContextHasNoValueError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_loop_max_exhausted_error_raises():
    """LoopMaxExhaustedError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(LoopMaxExhaustedError(), PypyrError)

    with pytest.raises(LoopMaxExhaustedError) as err_info:
        raise LoopMaxExhaustedError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_pipeline_definition_error_raises():
    """PipelineDefinitionError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PipelineDefinitionError(), PypyrError)

    with pytest.raises(PipelineDefinitionError) as err_info:
        raise PipelineDefinitionError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_pipeline_not_found_error_raises():
    """PipelineNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PipelineNotFoundError(), PypyrError)

    with pytest.raises(PipelineNotFoundError) as err_info:
        raise PipelineNotFoundError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_plugin_error_raises():
    """Pypyr plugin error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PlugInError(), PypyrError)

    with pytest.raises(PlugInError) as err_info:
        raise PlugInError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_pymodule_not_found_error_raises():
    """PyModuleNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PyModuleNotFoundError(), PypyrError)

    with pytest.raises(PyModuleNotFoundError) as err_info:
        raise PyModuleNotFoundError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"

# -------------------------- Control of Flow Instructions ---------------------


def test_stop_step_group_error_raises():
    """StopErrorGroup error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(StopStepGroup(), Stop)

    with pytest.raises(StopStepGroup) as err_info:
        raise StopStepGroup("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_stop_pipeline_error_raises():
    """StopPipeline error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(StopPipeline(), Stop)

    with pytest.raises(StopPipeline) as err_info:
        raise StopPipeline("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_jump_control_of_flow_instruction_raises():
    """Jump instruction raises."""
    try:
        raise Jump(['one', 'two'], 'sg', 'fg', 'og')
    except Jump as err_info:
        assert isinstance(err_info, ControlOfFlowInstruction)
        assert err_info.groups == ['one', 'two']
        assert err_info.success_group == 'sg'
        assert err_info.failure_group == 'fg'
        assert err_info.original_config == 'og'


def test_call_control_of_flow_instruction_raises():
    """Call instruction raises."""
    try:
        raise Call(['one', 'two'], 'sg', 'fg', 'og')
    except Call as err_info:
        assert isinstance(err_info, ControlOfFlowInstruction)
        assert err_info.groups == ['one', 'two']
        assert err_info.success_group == 'sg'
        assert err_info.failure_group == 'fg'
        assert err_info.original_config == 'og'

# -------------------------- END Control of Flow Instructions -----------------
