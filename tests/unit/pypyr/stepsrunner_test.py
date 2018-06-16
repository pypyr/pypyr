"""stepsrunner.py unit tests."""
from pypyr.context import Context
from pypyr.errors import ContextError
import pypyr.stepsrunner
import pytest
from unittest.mock import call, patch

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


def get_test_pipeline():
    """Return an arbitrary pipeline definition"""
    return {
        'sg1': [
            'step1',
            'step2',
            {'step3key1': 'values3k1', 'step3key2': 'values3k2'},
            'step4'
        ],
        'sg2': False,
        'sg3': 77,
        'sg4': None
    }


def get_valid_test_pipeline():
    """Return an arbitrary pipeline definition"""
    return {
        'sg1': [
            'step1',
            'step2',
            {'name': 'step3key1',
             'in':
                {'in3k1_1': 'v3k1', 'in3k1_2': 'v3k2'}},
            'step4'
        ],
        'sg2': False,
        'sg3': 77,
        'sg4': None
    }
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

# ------------------------- get_pipeline_steps -------------------------------#


def test_get_pipeline_steps_pass():
    """Return named step group from pipeline"""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        steps = pypyr.stepsrunner.get_pipeline_steps(
            get_test_pipeline(), 'sg1')

    assert len(steps) == 4
    assert steps[0] == 'step1'
    assert steps[1] == 'step2'
    assert steps[2] == {'step3key1': 'values3k1', 'step3key2': 'values3k2'}
    assert steps[3] == 'step4'

    mock_logger_debug.assert_any_call("4 steps found under sg1 in "
                                      "pipeline definition.")


def test_get_pipeline_steps_not_found():
    """Can't find step group in pipeline"""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        steps = pypyr.stepsrunner.get_pipeline_steps(
            get_test_pipeline(), 'arb')
        assert steps is None

    mock_logger_debug.assert_any_call(
        "pipeline doesn't have a arb collection. Add a arb: sequence to the "
        "yaml if you want arb actually to do something.")


def test_get_pipeline_steps_none():
    """Find step group in pipeline but it has no steps"""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'warn') as mock_logger_warn:
        steps = pypyr.stepsrunner.get_pipeline_steps(
            get_test_pipeline(), 'sg4')
        assert steps is None

    mock_logger_warn.assert_called_once_with(
        "sg4: sequence has no elements. So it won't do anything.")
# ------------------------- get_pipeline_steps--------------------------------#

# ------------------------- get_step_input_context----------------------------#


def test_get_step_input_context_no_in():
    """Get step context does nothing if no in key found."""
    context = get_test_context()
    pypyr.stepsrunner.get_step_input_context(None, context)

    assert context == get_test_context()


def test_get_step_input_context_in_empty():
    """Get step context does nothing if in key found but it's empty."""
    context = get_test_context()
    pypyr.stepsrunner.get_step_input_context({}, context)

    assert context == get_test_context()


def test_get_step_input_context_with_in():
    """Get step context adds in to context."""
    context = get_test_context()
    original_len = len(context)
    in_args = {'newkey1': 'v1',
               'newkey2': 'v2',
               'key3': 'updated in',
               'key4': [0, 1, 2, 3],
               'key5': True,
               'key6': False,
               'key7': 88}
    pypyr.stepsrunner.get_step_input_context(in_args, context)

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

# ------------------------- get_step_input_context----------------------------#

# ------------------------- run_failure_step_group----------------------------#


def test_run_failure_step_group_pass():
    """Failure step group runner passes on_failure to step group runner."""
    with patch('pypyr.stepsrunner.run_step_group') as mock_run_group:
        pypyr.stepsrunner.run_failure_step_group({'pipe': 'val'}, Context())

    mock_run_group.assert_called_once_with(pipeline_definition={'pipe': 'val'},
                                           step_group_name='on_failure',
                                           context=Context())


def test_run_failure_step_group_swallows():
    """Failure step group runner swallows errors."""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')

    with patch('pypyr.stepsrunner.run_step_group') as mock_run_group:
        with patch.object(logger, 'error') as mock_logger_error:
            mock_run_group.side_effect = ContextError('arb error')
            pypyr.stepsrunner.run_failure_step_group(
                {'pipe': 'val'}, Context())

        mock_logger_error.assert_any_call(
            "Failure handler also failed. Swallowing.")

    mock_run_group.assert_called_once_with(pipeline_definition={'pipe': 'val'},
                                           step_group_name='on_failure',
                                           context=Context())

# ------------------------- run_failure_step_group----------------------------#

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

# ------------------------- run_pipeline_steps--------------------------------#


def test_run_pipeline_steps_none():
    """If steps None does nothing"""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(None, Context({'k1': 'v1'}))

    mock_logger_debug.assert_any_call("No steps found to execute.")


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex(mock_run_step):
    """Complex step run with no in args."""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(
            [{'name': 'step1'}], Context({'k1': 'v1'}))

    mock_logger_debug.assert_any_call("{'name': 'step1'} is complex.")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'k1': 'v1'})


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_in(mock_run_step):
    """Complex step run with in args. In args added to context for run_step."""
    steps = [{
        'name': 'step1',
        'in': {'newkey1': 'v1',
               'newkey2': 'v2',
               'key3': 'updated in',
               'key4': [0, 1, 2, 3],
               'key5': True,
               'key6': False,
               'key7': 88}
    }]
    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
                                    'key2': 'value2',
                                    'key3': 'updated in',
                                    'key4': [0, 1, 2, 3],
                                    'key5': True,
                                    'key6': False,
                                    'key7': 88,
                                    'newkey1': 'v1',
                                    'newkey2': 'v2'})

    # validate all the in params ended up in context as intended
    assert len(context) - 2 == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_true(mock_run_step):
    """Complex step with run decorator set true will run step."""
    steps = [{
        'name': 'step1',
        'run': True
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
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


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_false(mock_run_step):
    """Complex step with run decorator set false doesn't run step."""
    steps = [{
        'name': 'step1',
        'run': False
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_run_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_str_formatting_false(
        mock_run_step):
    """Complex step with run formatting expression false doesn't run step."""
    steps = [{
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': '{key1}'
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_run_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_str_false(
        mock_run_step):
    """Complex step with run set to string False doesn't run step."""
    steps = [{
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': 'False'
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_run_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_str_lower_false(
        mock_run_step):
    """Complex step with run set to string false doesn't run step."""
    steps = [{
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': 'false'
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_run_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_bool_formatting_false(
        mock_run_step):
    """Complex step with run formatting expression false doesn't run step."""
    steps = [{
        'name': 'step1',
        # key5 will evaluate False because it's a bool and it's False
        'run': '{key5}'
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_run_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_bool_formatting_true(
        mock_run_step):
    """Complex step with run formatting expression true runs step."""
    steps = [{
        'name': 'step1',
        # key6 will evaluate True because it's a bool and it's True
        'run': '{key6}'
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
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


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_string_true(
        mock_run_step):
    """Complex step with run formatting expression True runs step."""
    steps = [{
        'name': 'step1',
        # 'True' will evaluate bool True
        'run': 'True'
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
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


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_1_true(
        mock_run_step):
    """Complex step with run 1 runs step."""
    steps = [{
        'name': 'step1',
        # 1 will evaluate True because it's an int and 1
        'run': 1
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
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


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_99_true(
        mock_run_step):
    """Complex step with run 99 runs step."""
    steps = [{
        'name': 'step1',
        # 1 will evaluate True because it's an int and > 0
        'run': 99
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
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


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_run_neg1_true(
        mock_run_step):
    """Complex step with run -1 runs step."""
    steps = [{
        'name': 'step1',
        # 1 will evaluate True because it's an int and > 0
        'run': -1
    }]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'key1': 'value1',
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


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_mix_run_and_not_run(
        mock_run_step):
    """Complex steps, some run some don't."""
    # Step 1 & 3 runs, 2 should not.
    steps = [{
        'name': 'step1',
        'run': True
    },
        {
        'name': 'step2',
        'run': False
    },
        {
        'name': 'step3',
    },
    ]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        with patch.object(logger, 'info') as mock_logger_info:
            pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 3 steps")
    mock_logger_info.assert_any_call(
        "step2 not running because run is False.")

    assert mock_run_step.call_count == 2
    assert mock_run_step.mock_calls == [call(context={
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3', 'key4':
        [
            {
                'k4lk1': 'value4',
                'k4lk2': 'value5'},
            {
                'k4lk1': 'value6',
                'k4lk2': 'value7'
            }],
        'key5': False,
        'key6': True,
        'key7': 77},
        step_name='step1'),
        call(context={
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3', 'key4':
            [
                {
                    'k4lk1': 'value4',
                    'k4lk2': 'value5'},
                {
                    'k4lk1': 'value6',
                    'k4lk2': 'value7'
                }],
            'key5': False,
            'key6': True,
            'key7': 77},
            step_name='step3')]

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_complex_with_multistep_none_run(
        mock_run_step):
    """Multiple steps and none run."""
    # None of these should run - various shades of python false
    steps = [{
        'name': 'step1',
        'run': False
    },
        {
        'name': 'step2',
        'run': 0
    },
        {
        'name': 'step3',
        'run': None,
    },
    ]

    context = get_test_context()
    original_len = len(context)

    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_logger_info.assert_any_call(
        "step2 not running because run is False.")
    mock_logger_info.assert_any_call(
        "step3 not running because run is False.")
    mock_run_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.stepsrunner.run_pipeline_step')
def test_run_pipeline_steps_simple(mock_run_step):
    """Simple step run."""
    logger = pypyr.log.logger.get_logger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(['step1'], {'k1': 'v1'})

    mock_logger_debug.assert_any_call('step1 is a simple string.')
    mock_run_step.assert_called_once_with(
        step_name='step1', context={'k1': 'v1'})
# ------------------------- run_pipeline_steps--------------------------------#

# ------------------------- run_step_group------------------------------------#


@patch('pypyr.stepsrunner.run_pipeline_steps')
def test_run_step_group_pass(mock_run_steps):
    """run_step_groups gets and runs steps for group."""
    pypyr.stepsrunner.run_step_group(
        pipeline_definition=get_valid_test_pipeline(),
        step_group_name='sg1',
        context=Context())

    mock_run_steps.assert_called_once_with(steps=[
        'step1',
        'step2',
        {'name': 'step3key1',
         'in':
            {'in3k1_1': 'v3k1', 'in3k1_2': 'v3k2'}},
        'step4'
    ], context=Context())
# ------------------------- run_step_group------------------------------------#
