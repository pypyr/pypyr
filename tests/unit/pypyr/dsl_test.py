"""dsl.py unit tests."""
import logging
import pytest
from unittest.mock import patch
from pypyr.context import Context
from pypyr.dsl import Step

# ------------------- test context -------------------------------------------#


def get_test_context():
    """Return a pypyr context for testing."""
    return Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': [
            {'k4lk1': 'value4',
             'k4lk2': 'value5'},
            {'k4lk1': 'value6',
             'k4lk2': 'value7'}
        ],
        'key5': False,
        'key6': True,
        'key7': 77
    })

# ------------------- test context -------------------------------------------#

# ------------------- step mocks ---------------------------------------------#


def mock_run_step(context):
    """Arbitrary mock function to execute instead of run_step"""
    context['test_run_step'] = 'this was set in step'


def mock_run_step_empty_context(context):
    """Clear the context in the step."""
    context.clear()


def mock_run_step_none_context(context):
    """None the context in the step"""
    # ignore the context is not used flake8 warning
    context = None  # noqa: F841
# ------------------- step mocks ---------------------------------------------#

# ------------------- Step----------------------------------------------------#
# ------------------- Step: init ---------------------------------------------#


@patch('pypyr.moduleloader.get_module', return_value='iamamodule')
def test_simple_step_init_defaults(mocked_moduleloader):
    """Simple step initializes with defaults as expected."""
    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step = Step('blah')

    mock_logger_debug.assert_any_call("blah is a simple string.")

    assert step.name == 'blah'
    assert step.module == 'iamamodule'
    assert step.in_parameters is None
    assert step.run_me
    assert not step.skip_me
    assert not step.swallow_me

    mocked_moduleloader.assert_called_once_with('blah')


@patch('pypyr.moduleloader.get_module', return_value='iamamodule')
def test_complex_step_init_defaults(mocked_moduleloader):
    """Complex step initializes with defaults as expected."""
    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step = Step({'name': 'blah'})

    mock_logger_debug.assert_any_call("blah is complex.")

    assert step.name == 'blah'
    assert step.module == 'iamamodule'
    assert step.in_parameters is None
    assert step.run_me
    assert not step.skip_me
    assert not step.swallow_me

    mocked_moduleloader.assert_called_once_with('blah')


@patch('pypyr.moduleloader.get_module', return_value='iamamodule')
def test_complex_step_init_with_decorators(mocked_moduleloader):
    """Complex step initializes with decorators set."""
    step = Step({'name': 'blah',
                 'in': {'k1': 'v1', 'k2': 'v2'},
                 'run': False,
                 'skip': True,
                 'swallow': True,
                 })
    assert step.name == 'blah'
    assert step.module == 'iamamodule'
    assert step.in_parameters == {'k1': 'v1', 'k2': 'v2'}
    assert not step.run_me
    assert step.skip_me
    assert step.swallow_me

    mocked_moduleloader.assert_called_once_with('blah')

# ------------------- Step: init ---------------------------------------------#

# ------------------- Step: invoke_step---------------------------------------#


@patch('pypyr.moduleloader.get_module')
def test_invoke_step_pass(mocked_moduleloader):
    """run_pipeline_step test pass."""
    step = Step('mocked.step')
    step.invoke_step(get_test_context())

    mocked_moduleloader.assert_called_once_with('mocked.step')
    mocked_moduleloader.return_value.run_step.assert_called_once_with(
        {'key1': 'value1',
         'key2': 'value2',
         'key3': 'value3',
         'key4': [
             {'k4lk1': 'value4', 'k4lk2': 'value5'},
             {'k4lk1': 'value6', 'k4lk2': 'value7'}],
         'key5': False,
         'key6': True,
         'key7': 77})


@patch('pypyr.moduleloader.get_module', return_value=3)
def test_invoke_step_no_run_step(mocked_moduleloader):
    """run_pipeline_step fails if no run_step on imported module."""
    step = Step('mocked.step')

    with pytest.raises(AttributeError) as err_info:
        step.invoke_step(get_test_context())

    mocked_moduleloader.assert_called_once_with('mocked.step')

    assert repr(err_info.value) == (
        "AttributeError(\"'int' object has no attribute 'run_step'\",)")


@patch('pypyr.moduleloader.get_module')
def test_invoke_step_context_abides(mocked_moduleloader):
    """Step mutates context & mutation abides after run_pipeline_step."""
    mocked_moduleloader.return_value.run_step = mock_run_step
    context = get_test_context()

    step = Step('mocked.step')
    step.invoke_step(context)

    mocked_moduleloader.assert_called_once_with('mocked.step')
    assert context['test_run_step'] == 'this was set in step'


@patch('pypyr.moduleloader.get_module')
def test_invoke_step_empty_context(mocked_moduleloader):
    """Empty context in step (i.e count == 0, but not is None)"""
    mocked_moduleloader.return_value.run_step = mock_run_step_empty_context
    context = get_test_context()

    step = Step('mocked.step')
    step.invoke_step(context)

    mocked_moduleloader.assert_called_once_with('mocked.step')
    assert len(context) == 0
    assert context is not None


@patch('pypyr.moduleloader.get_module')
def test_invoke_step_none_context(mocked_moduleloader):
    """Step rebinding context to None doesn't affect the caller Context."""
    mocked_moduleloader.return_value.run_step = mock_run_step_none_context
    context = get_test_context()

    step = Step('mocked.step')
    step.invoke_step(False)

    mocked_moduleloader.assert_called_once_with('mocked.step')
    assert context == {'key1': 'value1',
                       'key2': 'value2',
                       'key3': 'value3',
                       'key4': [
                           {'k4lk1': 'value4', 'k4lk2': 'value5'},
                           {'k4lk1': 'value6', 'k4lk2': 'value7'}],
                       'key5': False,
                       'key6': True,
                       'key7': 77}

# ------------------- Step: invoke_step---------------------------------------#

# ------------------- Step: run_step: run ------------------------------------#


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_true(mock_invoke_step,
                                                  mock_get_module):
    """Complex step with run decorator set true will run step."""
    step = Step({'name': 'step1',
                 'run': True})

    context = get_test_context()
    original_len = len(context)

    step.run_step(context)

    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_false(mock_invoke_step,
                                                   mock_get_module):
    """Complex step with run decorator set false doesn't run step."""
    step = Step({'name': 'step1',
                 'run': False})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call("step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_str_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run formatting expression false doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': '{key1}'})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call("step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_str_false(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with run set to string False doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': 'False'})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_str_lower_false(mock_invoke_step,
                                                             mock_get_module):
    """Complex step with run set to string false doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': 'false'})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_bool_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run formatting expression false doesn't run step."""
    step = Step({
        'name': 'step1',
                # key5 will evaluate False because it's a bool and it's False
                'run': '{key5}'})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_bool_formatting_true(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run formatting expression true runs step."""
    step = Step({
        'name': 'step1',
        # key6 will evaluate True because it's a bool and it's True
        'run': '{key6}'})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_string_true(mock_invoke_step,
                                                         mock_get_module):
    """Complex step with run formatting expression True runs step."""
    step = Step({
        'name': 'step1',
        # 'True' will evaluate bool True
        'run': 'True'})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_1_true(mock_invoke_step,
                                                    mock_get_module):
    """Complex step with run 1 runs step."""
    step = Step({
        'name': 'step1',
        # 1 will evaluate True because it's an int and 1
        'run': 1})

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_99_true(mock_invoke_step,
                                                     mock_get_module):
    """Complex step with run 99 runs step."""
    step = Step({
        'name': 'step1',
        # 99 will evaluate True because it's an int and > 0
        'run': 99
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_neg1_true(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with run -1 runs step."""
    step = Step({
        'name': 'step1',
        # -1 will evaluate True because it's an int and != 0
        'run': -1
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len

# ------------------- Step: run_step: run ------------------------------------#


# ------------------- Step: run_step: skip -----------------------------------#
@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_false(mock_invoke_step,
                                                    mock_get_module):
    """Complex step with skip decorator set false will run step."""
    step = Step({
        'name': 'step1',
        'skip': False
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_true(mock_invoke_step,
                                                   mock_get_module):
    """Complex step with skip decorator set true runa step."""
    step = Step({
        'name': 'step1',
        'skip': True
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_str_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip formatting expression false doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate True
        'skip': '{key6}'
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_str_true(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with skip set to string False doesn't run step."""
    step = Step({
        'name': 'step1',
        # skip evaluates True because it's a string and TRUE parses to True.
        'skip': 'TRUE'
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_str_lower_true(mock_invoke_step,
                                                             mock_get_module):
    """Complex step with run set to string true doesn't run step."""
    step = Step({
        'name': 'step1',
        # skip will evaluate true because it's a string and true is True.
        'skip': 'true'
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_and_skip_bool_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run doesn't run step, evals before skip."""
    step = Step({
        'name': 'step1',
        # key5 will evaluate False because it's a bool and it's False
        'run': '{key5}',
        'skip': True
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_bool_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip formatting expression true runs step."""
    step = Step({
        'name': 'step1',
        # key5 will evaluate False because it's a bool and it's False
        'skip': '{key5}'
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_string_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip formatting expression False runs step."""
    step = Step({
        'name': 'step1',
        # 'False' will evaluate bool False
        'skip': 'False'
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_0_true(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run 1 runs step."""
    step = Step({
        'name': 'step1',
        # 0 will evaluate False because it's an int and 0
        'skip': 0
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_99_true(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip 99 doesn't run step."""
    step = Step({
        'name': 'step1',
        # 99 will evaluate True because it's an int and > 0
        'skip': 99
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_neg1_true(mock_invoke_step,
                                                        mock_get_module):
    """Complex step with run -1 runs step."""
    step = Step({
        'name': 'step1',
        # -1 will evaluate True because it's an int and != 0
        'skip': -1
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call("step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


# ------------------- Step: run_step: skip -----------------------------------#

# ------------------- Step: run_step: swallow --------------------------------#
@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_swallow_true(mock_invoke_step,
                                                 mock_get_module):
    """Complex step with swallow true runs normally even without error."""
    step = Step({
        'name': 'step1',
        'swallow': True
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_swallow_false(mock_invoke_step,
                                                  mock_get_module):
    """Complex step with swallow false runs normally even without error."""
    step = Step({
        'name': 'step1',
        'swallow': False
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_complex_swallow_true_error(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with swallow true swallows error."""
    step = Step({
        'name': 'step1',
        'swallow': 1
    })

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        with patch.object(logger, 'error') as mock_logger_error:
            step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_logger_error.assert_called_once_with(
        "step1 Ignoring error because swallow is True "
        "for this step.\n"
        "ValueError: arb error here")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_complex_swallow_false_error(mock_invoke_step,
                                                        mock_get_module):
    """Complex step with swallow false raises error."""
    step = Step({
        'name': 'step1',
        'swallow': 0
    })

    context = get_test_context()
    original_len = len(context)

    with pytest.raises(ValueError) as err_info:
        step.run_step(context)

        assert repr(err_info.value) == ("ValueError(\'arb error here',)")

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_complex_swallow_defaults_false_error(
        mock_invoke_step,
        mock_get_module):
    """Complex step with swallow not specified still raises error."""
    step = Step({
        'name': 'step1'
    })

    context = get_test_context()
    original_len = len(context)

    with pytest.raises(ValueError) as err_info:
        step.run_step(context)

        assert repr(err_info.value) == ("ValueError(\'arb error here',)")

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_simple_with_error(mock_invoke_step,
                                              mock_get_module):
    """Simple step run with error should not swallow."""
    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        step = Step('step1')
        with pytest.raises(ValueError) as err_info:
            step.run_step(Context({'k1': 'v1'}))

            assert repr(err_info.value) == (
                "ValueError(\'arb error here',)")

    mock_logger_debug.assert_any_call('step1 is a simple string.')
    mock_invoke_step.assert_called_once_with(
        context={'k1': 'v1'})

# ------------------- Step: run_step: swallow --------------------------------#

# ------------------- Step: set_step_input_context ---------------------------#


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_no_in_simple(mocked_moduleloader):
    """Set step context does nothing if no in key found in simple step."""
    step = Step('blah')
    context = get_test_context()
    step.set_step_input_context(context)

    assert context == get_test_context()


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_no_in_complex(mocked_moduleloader):
    """Set step context does nothing if no in key found in complex step."""
    step = Step({'name': 'blah'})
    context = get_test_context()
    step.set_step_input_context(context)

    assert context == get_test_context()


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_in_empty(mocked_moduleloader):
    """Set step context does nothing if in key found but it's empty."""
    step = Step({'name': 'blah', 'in': {}})
    context = get_test_context()
    step.set_step_input_context(context)

    assert context == get_test_context()


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_with_in(mocked_moduleloader):
    """Set step context adds in to context."""
    context = get_test_context()
    original_len = len(context)
    in_args = {'newkey1': 'v1',
               'newkey2': 'v2',
               'key3': 'updated in',
               'key4': [0, 1, 2, 3],
               'key5': True,
               'key6': False,
               'key7': 88}
    step = Step({'name': 'blah', 'in': in_args})
    step.set_step_input_context(context)

    assert len(context) - 2 == original_len
    assert context['newkey1'] == 'v1'
    assert context['newkey2'] == 'v2'
    assert context['key1'] == 'value1'
    assert context['key2'] == 'value2'
    assert context['key3'] == 'updated in'
    assert context['key4'] == [0, 1, 2, 3]
    assert context['key5']
    assert not context['key6']
    assert context['key7'] == 88

# ------------------- Step: set_step_input_context ---------------------------#
# ------------------- Step----------------------------------------------------#
