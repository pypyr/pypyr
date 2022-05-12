"""errors.py unit tests."""
import pytest

from pypyr.errors import Error as PypyrError
from pypyr.errors import (
    ContextError,
    get_error_name,
    HandledError,
    KeyInContextHasNoValueError,
    KeyNotInContextError,
    LoopMaxExhaustedError,
    MultiError,
    PlugInError,
    PipelineDefinitionError,
    PipelineNotFoundError,
    PyModuleNotFoundError,
    Stop,
    StopStepGroup,
    StopPipeline,
    SubprocessError,
    ControlOfFlowInstruction,
    Call,
    Jump)


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
    """A ContextError raises with correct message."""
    assert isinstance(ContextError(), PypyrError)

    with pytest.raises(ContextError) as err_info:
        raise ContextError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_handled_error_raises():
    """A HandledError raises with correct message and with from."""
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
    """A LoopMaxExhaustedError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(LoopMaxExhaustedError(), PypyrError)

    with pytest.raises(LoopMaxExhaustedError) as err_info:
        raise LoopMaxExhaustedError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_pipeline_definition_error_raises():
    """A PipelineDefinitionError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PipelineDefinitionError(), PypyrError)

    with pytest.raises(PipelineDefinitionError) as err_info:
        raise PipelineDefinitionError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_pipeline_not_found_error_raises():
    """A PipelineNotFoundError error raises with correct message."""
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
    """A PyModuleNotFoundError error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(PyModuleNotFoundError(), PypyrError)

    with pytest.raises(PyModuleNotFoundError) as err_info:
        raise PyModuleNotFoundError("this is error text right here")

    assert str(err_info.value) == "this is error text right here"

# region MultiError


def test_multierror():
    """Raise a MultiError."""
    me = MultiError()
    assert isinstance(me, PypyrError)

    assert not me.has_errors

    assert len(me) == 0

    # empty repr
    assert repr(me) == 'MultiError()'

    for m in me:
        raise AssertionError('nothing to iterate')

    # append
    me.append(ValueError('one'))
    assert len(me) == 1
    assert me.has_errors
    assert str(me) == "An error occurred:\nValueError: one"

    me.append(SubprocessError(123, "cmd"))
    assert str(me) == (
        "Multiple error(s) occurred:\nValueError: one\n"
        + "SubprocessError: Command 'cmd' returned non-zero exit status 123.")
    assert len(me) == 2
    assert me.has_errors

    #  iterate
    out = [str(m) for m in me]
    assert out == ['one', "Command 'cmd' returned non-zero exit status 123."]

    # index getter
    assert repr(me[0]) == "ValueError('one')"
    assert me[1].returncode == 123

    # repr with errs but no msg
    assert repr(me) == (
        "MultiError(errors=[ValueError('one'), "
        + "SubprocessError(returncode=123, cmd='cmd')])")

    # extend
    me.extend([AssertionError('blah'), KeyError('ke')])
    assert len(me) == 4

    # with msg
    me = MultiError("msg")
    assert str(me) == 'msg'
    assert repr(me) == "MultiError(message='msg')"

    me.append(ValueError('one'))
    assert str(me) == "msg\nValueError: one"
    assert repr(me) == "MultiError(message='msg', errors=[ValueError('one')])"

    # raises
    with pytest.raises(MultiError) as err:
        raise me

    assert repr(err.value[0]) == "ValueError('one')"

# endregion MultiError

# region SubprocessError


def test_subprocess_error_raises():
    """Raise SubprocessError."""
    assert isinstance(SubprocessError(0, 'cmd'), PypyrError)

    with pytest.raises(SubprocessError) as err_caught:
        raise SubprocessError(0, 'cmd')

    err = err_caught.value
    assert err.returncode == 0
    assert err.cmd == 'cmd'
    assert err.stdout is None
    assert err.stderr is None


def test_subprocess_error_repr():
    """Convert to repr SubprocessError."""
    err_repr = repr(SubprocessError(-123, 'cmd'))
    rehydrated = eval(err_repr)

    assert rehydrated.returncode == -123
    assert rehydrated.cmd == 'cmd'
    assert rehydrated.stdout is None
    assert rehydrated.stderr is None

    err_repr = repr(SubprocessError(123, 'cmd', 'std out'))
    rehydrated = eval(err_repr)

    assert rehydrated.returncode == 123
    assert rehydrated.cmd == 'cmd'
    assert rehydrated.stdout == 'std out'
    assert rehydrated.stderr is None

    err_repr = repr(SubprocessError(123, 'cmd', 'std out', 'std err'))
    rehydrated = eval(err_repr)

    assert rehydrated.returncode == 123
    assert rehydrated.cmd == 'cmd'
    assert rehydrated.stdout == 'std out'
    assert rehydrated.stderr == 'std err'


def test_subprocess_error_str():
    """Convert to str SubprocessError."""
    #  known signal
    err_str = str(SubprocessError(-2, 'cmd'))
    assert err_str == "Command 'cmd' died with <Signals.SIGINT: 2>."

    #  unknown signal
    err_str = str(SubprocessError(-999, 'cmd'))
    assert err_str == "Command 'cmd' died with unknown signal 999."

    # return-code > 0
    err_str = str(SubprocessError(1, 'cmd'))
    assert err_str == "Command 'cmd' returned non-zero exit status 1."

    # return-code > 0 with stderr str.
    err_str = str(SubprocessError(1, 'cmd', stderr='blah'))
    assert err_str == (
        "Command 'cmd' returned non-zero exit status 1. stderr: blah")

    # return-code > 0 with stderr bytes.
    err_str = str(SubprocessError(1, 'cmd', stderr=b'blah'))
    assert err_str == (
        "Command 'cmd' returned non-zero exit status 1. stderr: b'blah'")

# endregion SubprocessError

# region Control of Flow Instructions


def test_stop_step_group_error_raises():
    """A StopErrorGroup error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(StopStepGroup(), Stop)

    with pytest.raises(StopStepGroup) as err_info:
        raise StopStepGroup("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_stop_pipeline_error_raises():
    """A StopPipeline error raises with correct message."""
    # confirm subclassed from pypyr root error
    assert isinstance(StopPipeline(), Stop)

    with pytest.raises(StopPipeline) as err_info:
        raise StopPipeline("this is error text right here")

    assert str(err_info.value) == "this is error text right here"


def test_jump_control_of_flow_instruction_raises():
    """A Jump instruction raises."""
    try:
        raise Jump(['one', 'two'], 'sg', 'fg', 'og')
    except Jump as err_info:
        assert isinstance(err_info, ControlOfFlowInstruction)
        assert err_info.groups == ['one', 'two']
        assert err_info.success_group == 'sg'
        assert err_info.failure_group == 'fg'
        assert err_info.original_config == 'og'


def test_call_control_of_flow_instruction_raises():
    """A Call instruction raises."""
    try:
        raise Call(['one', 'two'], 'sg', 'fg', 'og')
    except Call as err_info:
        assert isinstance(err_info, ControlOfFlowInstruction)
        assert err_info.groups == ['one', 'two']
        assert err_info.success_group == 'sg'
        assert err_info.failure_group == 'fg'
        assert err_info.original_config == 'og'

# endregion Control of Flow Instructions
