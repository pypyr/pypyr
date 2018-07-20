"""stepsrunner.py unit tests."""
import logging
import pytest
from unittest.mock import call, patch
from pypyr.context import Context
from pypyr.dsl import Step
from pypyr.errors import ContextError
import pypyr.stepsrunner

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

# ------------------------- get_pipeline_steps -------------------------------#


def test_get_pipeline_steps_pass():
    """Return named step group from pipeline"""
    logger = logging.getLogger('pypyr.stepsrunner')
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
    logger = logging.getLogger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        steps = pypyr.stepsrunner.get_pipeline_steps(
            get_test_pipeline(), 'arb')
        assert steps is None

    mock_logger_debug.assert_any_call(
        "pipeline doesn't have a arb collection. Add a arb: sequence to the "
        "yaml if you want arb actually to do something.")


def test_get_pipeline_steps_none():
    """Find step group in pipeline but it has no steps"""
    logger = logging.getLogger('pypyr.stepsrunner')
    with patch.object(logger, 'warn') as mock_logger_warn:
        steps = pypyr.stepsrunner.get_pipeline_steps(
            get_test_pipeline(), 'sg4')
        assert steps is None

    mock_logger_warn.assert_called_once_with(
        "sg4: sequence has no elements. So it won't do anything.")
# ------------------------- get_pipeline_steps--------------------------------#

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
    logger = logging.getLogger('pypyr.stepsrunner')

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

# ------------------------- run_pipeline_steps--------------------------------#


def test_run_pipeline_steps_none():
    """If steps None does nothing"""
    logger = logging.getLogger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(None, Context({'k1': 'v1'}))

    mock_logger_debug.assert_any_call("No steps found to execute.")


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex(mock_invoke_step, mock_module):
    """Complex step run with no in args."""
    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(
            [{'name': 'step1'}], Context({'k1': 'v1'}))

    mock_logger_debug.assert_any_call("step1 is complex.")
    mock_invoke_step.assert_called_once_with(context={'k1': 'v1'})


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_in(mock_invoke_step, mock_module):
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

    logger = logging.getLogger('pypyr.stepsrunner')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    mock_invoke_step.assert_called_once_with(context={'key1': 'value1',
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

# -----------------------  run_pipeline_steps: run ---------------------------#


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_mix_run_and_not_run(mock_invoke_step, mock_module):
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

    logger_steps = logging.getLogger('pypyr.stepsrunner')
    logger_dsl = logging.getLogger('pypyr.dsl')
    with patch.object(logger_steps, 'debug') as mock_logger_debug:
        with patch.object(logger_dsl, 'info') as mock_logger_info:
            pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 3 steps")
    mock_logger_info.assert_any_call(
        "step2 not running because run is False.")

    assert mock_invoke_step.call_count == 2
    assert mock_invoke_step.mock_calls == [call(context={
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
        'key7': 77}),
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
            'key7': 77})]

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_multistep_none_run(mock_invoke_step,
                                                            mock_module):
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

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_logger_info.assert_any_call(
        "step2 not running because run is False.")
    mock_logger_info.assert_any_call(
        "step3 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len
# -----------------------  run_pipeline_steps: run ---------------------------#

# -----------------------  run_pipeline_steps: skip --------------------------#


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_mix_skip_and_not_skip(mock_invoke_step,
                                                  mock_module):
    """Complex steps, some run some don't."""
    # Step 1 & 3 runs, 2 should not.
    steps = [{
        'name': 'step1',
        'skip': False
    },
        {
        'name': 'step2',
        'skip': True
    },
        {
        'name': 'step3',
    },
    ]

    context = get_test_context()
    original_len = len(context)

    logger_steps = logging.getLogger('pypyr.stepsrunner')
    logger_dsl = logging.getLogger('pypyr.dsl')
    with patch.object(logger_steps, 'debug') as mock_logger_debug:
        with patch.object(logger_dsl, 'info') as mock_logger_info:
            pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 3 steps")
    mock_logger_info.assert_any_call(
        "step2 not running because skip is True.")

    assert mock_invoke_step.call_count == 2
    assert mock_invoke_step.mock_calls == [call(context={
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
        'key7': 77}),
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
            'key7': 77})]

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_multistep_all_skip(mock_invoke_step,
                                                            mock_module):
    """Multiple steps and none run."""
    # None of these should run - various shades of python true
    steps = [{
        'name': 'step1',
        'skip': [1, 2, 3]
    },
        {
        'name': 'step2',
        'skip': 1
    },
        {
        'name': 'step3',
        'skip': True,
    },
        {
        'name': 'step4',
        # run evals before skip
        'run': False,
        'skip': False
    },
    ]

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.stepsrunner.run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_logger_info.assert_any_call(
        "step2 not running because skip is True.")
    mock_logger_info.assert_any_call(
        "step3 not running because skip is True.")
    mock_logger_info.assert_any_call(
        "step4 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len

# -----------------------  END run_pipeline_steps: skip ----------------------#

# -----------------------  run_pipeline_steps: swallow -----------------------#


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_swallow_sequence(mock_invoke_step, mock_module):
    """Complex steps, some run some don't, some swallow, some don't."""
    # 1 & 2 don't run,
    # 3 runs, no error
    # 4 runs, error and swallows
    # 5 skips
    # 6 runs, error and raises
    # 7 doesn't run because execution stopped at 6 because of error
    mock_invoke_step.side_effect = [
        None,  # 3
        ValueError('arb error here 4'),  # 4
        ValueError('arb error here 6'),  # 6
    ]

    steps = [
        {
            'name': 'step1',
            'run': False
        },
        {
            'name': 'step2',
            'skip': True
        },
        {
            'name': 'step3',
        },
        {
            'name': 'step4',
            'run': True,
            'skip': False,
            'swallow': 1
        },
        {
            'name': 'step5',
            'run': True,
            'skip': True,
            'swallow': True
        },
        'step6',
        'step7',
    ]

    context = get_test_context()
    original_len = len(context)

    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        with patch.object(logger, 'info') as mock_logger_info:
            with patch.object(logger, 'error') as mock_logger_error:
                with pytest.raises(ValueError) as err_info:
                    pypyr.stepsrunner.run_pipeline_steps(steps, context)

                    assert repr(err_info.value) == (
                        "ValueError(\'arb error here 6',)")

    mock_logger_debug.assert_has_calls == [call('step1 is complex.'),
                                           call('step2 is complex.'),
                                           call('step3 is complex.'),
                                           call('step4 is complex.'),
                                           call('step5 is complex.'),
                                           call('step6 is a simple string.')]

    mock_logger_info.mock_calls == [
        call('step1 not running because run is False.'),
        call('step2 not running because skip is True.'),
        call('step5 not running because skip is True.')]

    mock_logger_error.assert_called_once_with(
        "step4 Ignoring error because swallow is True "
        "for this step.\n"
        "ValueError: arb error here 4")

    assert mock_invoke_step.call_count == 3
    assert mock_invoke_step.mock_calls == [call(context={
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
        'key7': 77}),
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
            'key7': 77}),
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
            'key7': 77})]

    # validate all the in params ended up in context as intended
    assert len(context) == original_len

# -----------------------  END run_pipeline_steps: swallow------------------#

# ------------------------- run_pipeline_steps--------------------------------#


@patch('pypyr.moduleloader.get_module', return_value='arbmodule')
@patch.object(Step, 'run_step')
def test_run_pipeline_steps_simple(mock_run_step, mock_module):
    """Simple step run."""
    logger = logging.getLogger('pypyr.dsl')
    with patch.object(logger, 'debug') as mock_logger_debug:
        pypyr.stepsrunner.run_pipeline_steps(['step1'], {'k1': 'v1'})

    mock_logger_debug.assert_any_call('step1 is a simple string.')
    mock_run_step.assert_called_once_with({'k1': 'v1'})


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
