"""stepsrunner.py unit tests."""
from pypyr.context import Context
import pypyr.stepsrunner
import pytest
from unittest.mock import patch

# ------------------------- test context--------------------------------------#


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

# ------------------------- test context--------------------------------------#

# ------------------------- step mocks ---------------------------------------#


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
# ------------------------- step mocks ---------------------------------------#


# ------------------------- run_pipeline_step---------------------------------#
@patch('pypyr.moduleloader.get_module')
def test_run_pipeline_step_pass(mocked_moduleloader):
    """run_pipeline_step test pass."""
    pypyr.stepsrunner.run_pipeline_step('mocked.step', get_test_context())

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
def test_run_pipeline_step_no_run_step(mocked_moduleloader):
    """run_pipeline_step fails if no run_step on imported module."""
    with pytest.raises(AttributeError) as err_info:
        pypyr.stepsrunner.run_pipeline_step('mocked.step', get_test_context)

    mocked_moduleloader.assert_called_once_with('mocked.step')

    assert repr(err_info.value) == (
        "AttributeError(\"'int' object has no attribute 'run_step'\",)")


@patch('pypyr.moduleloader.get_module')
def test_run_pipeline_step_context_abides(mocked_moduleloader):
    """Steps mutate context & mutation abides after run_pipeline_step."""
    mocked_moduleloader.return_value.run_step = mock_run_step
    context = get_test_context()

    pypyr.stepsrunner.run_pipeline_step('mocked.step', context)

    mocked_moduleloader.assert_called_once_with('mocked.step')
    assert context['test_run_step'] == 'this was set in step'


@patch('pypyr.moduleloader.get_module')
def test_run_pipeline_step_empty_context(mocked_moduleloader):
    """Empty context in step (i.e count == 0, but not is None)"""
    mocked_moduleloader.return_value.run_step = mock_run_step_empty_context
    context = get_test_context()

    pypyr.stepsrunner.run_pipeline_step('mocked.step', context)

    mocked_moduleloader.assert_called_once_with('mocked.step')
    assert len(context) == 0
    assert context is not None


@patch('pypyr.moduleloader.get_module')
def test_run_pipeline_step_none_context(mocked_moduleloader):
    """Step rebinding context to None doesn't affect the caller Context."""
    mocked_moduleloader.return_value.run_step = mock_run_step_none_context
    context = get_test_context()

    pypyr.stepsrunner.run_pipeline_step('mocked.step', False)

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
# ------------------------- run_pipeline_step---------------------------------#
