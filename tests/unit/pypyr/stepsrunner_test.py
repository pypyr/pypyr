"""stepsrunner.py unit tests."""
import logging

from unittest.mock import call, patch, Mock

import pytest

from pypyr.context import Context
from pypyr.dsl import Step
from pypyr.errors import (Call,
                          ContextError,
                          Jump,
                          Stop,
                          StopPipeline,
                          StopStepGroup)
from pypyr.pipedef import PipelineDefinition, PipelineBody, PipelineInfo
from pypyr.pipeline import Pipeline
from tests.common.utils import DeepCopyMagicMock, patch_logger


# region test context


def arb_step_mock(context):
    """No real reason, other than to mock the existence of a run_step."""
    return 'from arb step mock'


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
    """Return an arbitrary pipeline definition."""
    return {
        'sg1': [
            'step1',
            'step2',
            {'name': 'step3key1', 'in': {'key3k2': 'values3k2'}},
            'step4'
        ],
        'sg2': [],
        'sg3': [],
        'sg4': []
    }


def get_valid_test_pipeline():
    """Return an arbitrary pipeline definition."""
    return {
        'sg1': [
            'step1',
            'step2',
            {'name': 'step3key1',
             'in':
                {'in3k1_1': 'v3k1', 'in3k1_2': 'v3k2'}},
            'step4'
        ],
        'sg2': [],
        'sg3': [],
        'sg4': []
    }


def get_valid_steps_pipeline():
    """Pipeline definition where steps point to actual test step."""
    return {
        'sg1': [
            'tests.arbpack.arbincrementstep',
            'tests.arbpack.arbincrementstep'],
        'sg2': [
            'tests.arbpack.arbincrementstep',
        ],
        'sg3': []
    }

# endregion test context

# region init


def test_stepsrunner_init():
    """The StepsRunner initializes."""
    p = PipelineBody(context_parser='context parser', step_groups={'a': []})
    assert p.step_groups == {'a': []}
    assert p.context_parser == 'context parser'


# endregion init

# region get_pipeline_steps

@patch('pypyr.moduleloader.get_module')
def test_get_pipeline_steps_pass(mocked_module_get):
    """Return named step group from pipeline."""
    with patch_logger('pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
        steps = PipelineBody.from_mapping(
            get_test_pipeline()).get_pipeline_steps('sg1')
    assert len(steps) == 4
    assert steps[0] == Step('step1')
    assert steps[1] == Step('step2')
    assert steps[2] == Step('step3key1',
                            in_parameters=  {'key3k2': 'values3k2'})
    assert steps[3] == Step('step4')

    mock_logger_debug.assert_any_call("4 steps found under sg1 in "
                                      "pipeline definition.")


def test_get_pipeline_steps_not_found():
    """Can't find step group in pipeline."""
    with patch_logger('pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
        steps = PipelineBody.from_mapping(
            get_test_pipeline()).get_pipeline_steps('arb')
        assert steps is None

    mock_logger_debug.assert_any_call(
        "pipeline doesn't have a arb collection. Add a arb: sequence to the "
        "yaml if you want arb actually to do something.")


def test_get_pipeline_steps_none():
    """Find step group in pipeline but it has no steps."""
    with patch_logger(
            'pypyr.pipedef', logging.WARNING) as mock_logger_warn:
        steps = PipelineBody.from_mapping(
            get_test_pipeline()).get_pipeline_steps('sg4')
        assert steps is None

    mock_logger_warn.assert_called_once_with(
        "sg4: sequence has no elements. So it won't do anything.")
# endregion get_pipeline_steps

# region run_failure_step_group


def test_run_failure_step_group_pass():
    """Failure step group runner passes on_failure to step group runner."""
    with patch.object(PipelineBody,
                      'run_step_group') as mock_run_group:
        PipelineBody.from_mapping(
            {'pipe': []}).run_failure_step_group('on_failure', Context())

    mock_run_group.assert_called_once_with('on_failure',
                                           context={},
                                           raise_stop=True)


def test_run_failure_step_group_swallows():
    """Failure step group runner swallows errors."""
    with patch.object(PipelineBody,
                      'run_step_group') as mock_run_group:
        with patch_logger(
                'pypyr.pipedef', logging.ERROR) as mock_logger_error:
            mock_run_group.side_effect = ContextError('arb error')
            runner = PipelineBody.from_mapping({'pipe': []})
            runner.run_failure_step_group('arb_failure', Context())

        mock_logger_error.assert_any_call(
            "Failure handler also failed. Swallowing.")

    assert runner.step_groups == {'pipe': []}
    mock_run_group.assert_called_once_with('arb_failure',
                                           context={},
                                           raise_stop=True)


def test_run_failure_step_group_stop():
    """Failure step group runner does Stop."""
    with patch.object(PipelineBody,
                      'run_step_group') as mock_run_group:
        with patch_logger(
                'pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
            mock_run_group.side_effect = StopStepGroup
            runner = PipelineBody.from_mapping({'pipe': []})

            with pytest.raises(StopStepGroup):
                runner.run_failure_step_group('arb_failure', Context())

        mock_logger_debug.assert_any_call(
            "Stop instruction: done with failure handler arb_failure.")

    assert runner.step_groups == {'pipe': []}
    mock_run_group.assert_called_once_with('arb_failure',
                                           context={},
                                           raise_stop=True)

# endregion run_failure_step_group

# region run_pipeline_steps


def test_run_pipeline_steps_none():
    """If steps None does nothing."""
    with patch_logger('pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
        PipelineBody(step_groups={}).run_pipeline_steps(None,
                                                        Context({'k1': 'v1'}))

    mock_logger_debug.assert_any_call("No steps found to execute.")


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex(mock_invoke_step, mock_module):
    """Complex step run with no in args."""
    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        PipelineBody.from_mapping(
            {'steps' :[]}).run_pipeline_steps([
                Step.from_step_definition({'name': 'step1'})],
                Context({'k1': 'v1'}))

    mock_logger_debug.assert_any_call("step1 is complex.")
    mock_invoke_step.assert_called_once_with(context={'k1': 'v1'})


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_run_pipeline_steps_complex_with_in(mock_invoke_step, mock_module):
    """Complex step run with in args. In args added to context for run_step."""
    steps = [Step.from_step_definition({
        'name': 'step1',
        'in': {'newkey1': 'v1',
               'newkey2': 'v2',
               'key3': 'updated in',
               'key4': [0, 1, 2, 3],
               'key5': True,
               'key6': False,
               'key7': 88}
    })]
    context = Context({
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
        'key7': 77,
        'key8': None,
        'key9': 'arb'
    })

    with patch_logger('pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
        PipelineBody.from_mapping({}).run_pipeline_steps(steps, context)

    mock_logger_debug.assert_any_call("executed 1 steps")
    assert mock_invoke_step.call_count == 1
    # step invoked with the context updated from 'in'
    assert mock_invoke_step.call_args_list[0] == call(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'updated in',
                 'key4': [0, 1, 2, 3],
                 'key5': True,
                 'key6': False,
                 'key7': 88,
                 'key8': None,
                 'key9': 'arb',
                 'newkey1': 'v1',
                 'newkey2': 'v2'})

    # all items keys 'in' purged from context.
    assert context == {'key1': 'value1',
                       'key2': 'value2',
                       'key8': None,
                       'key9': 'arb'}


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_step')
def test_run_pipeline_steps_simple(mock_run_step, mock_module):
    """Simple step run."""
    PipelineBody.from_mapping({}).run_pipeline_steps([Step('step1')],
            Context( {'k1': 'v1'}))

    mock_run_step.assert_called_once_with({'k1': 'v1'})


# region run_pipeline_steps: run


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_mix_run_and_not_run(mock_invoke_step, mock_module):
    """Complex steps, some run some don't."""
    # Step 1 & 3 runs, 2 should not.
    steps = [Step.from_step_definition({
        'name': 'step1',
        'run': True
    }),
        Step.from_step_definition({
        'name': 'step2',
        'run': False
    }),
        Step.from_step_definition({
        'name': 'step3',
    }),
    ]

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
        with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
            PipelineBody.from_mapping({}).run_pipeline_steps(steps, context)

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


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_multistep_none_run(mock_invoke_step,
                                                            mock_module):
    """Multiple steps and none run."""
    # None of these should run - various shades of python false
    steps = [Step.from_step_definition({
        'name': 'step1',
        'run': False
    }),
        Step.from_step_definition({
        'name': 'step2',
        'run': 0
    }),
        Step.from_step_definition({
        'name': 'step3',
        'run': None,
    }),
    ]

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        PipelineBody.from_mapping({}).run_pipeline_steps(steps, context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_logger_info.assert_any_call(
        "step2 not running because run is False.")
    mock_logger_info.assert_any_call(
        "step3 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len
# endregion  run_pipeline_steps: run

# region  run_pipeline_steps: skip


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_mix_skip_and_not_skip(mock_invoke_step,
                                                  mock_module):
    """Complex steps, some run some don't."""
    # Step 1 & 3 runs, 2 should not.
    steps = [Step.from_step_definition({
        'name': 'step1',
        'skip': False
    }),
        Step.from_step_definition({
        'name': 'step2',
        'skip': True
    }),
        Step.from_step_definition({
        'name': 'step3',
    }),
    ]

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.pipedef', logging.DEBUG) as mock_logger_debug:
        with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
            PipelineBody.from_mapping({}).run_pipeline_steps(steps, context)

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


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_multistep_all_skip(mock_invoke_step,
                                                            mock_module):
    """Multiple steps and none run."""
    # None of these should run - various shades of python true
    steps = [Step.from_step_definition({
        'name': 'step1',
        'skip': [1, 2, 3]
    }),
        Step.from_step_definition({
        'name': 'step2',
        'skip': 1
    }),
        Step.from_step_definition({
        'name': 'step3',
        'skip': True,
    }),
        Step.from_step_definition({
        'name': 'step4',
        # run evals before skip
        'run': False,
        'skip': False
    }),
    ]

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        PipelineBody.from_mapping({}).run_pipeline_steps(steps, context)

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

# endregion run_pipeline_steps: skip

# region run_pipeline_steps: swallow


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_run_pipeline_steps_swallow_sequence(mock_invoke_step, mock_module):
    """Complex steps, some run some don't, some swallow, some don't."""
    step4_run_error_swallow = {
        'col': None,
        'customError': {},
        'description': 'arb error here 4',
        'exception': ValueError('arb error here 4'),
        'line': None,
        'name': 'ValueError',
        'step': 'step4',
        'swallowed': True,
    }

    step6_run_error_raise = {
        'col': None,
        'customError': {},
        'description': 'arb error here 6',
        'exception': ValueError('arb error here 6'),
        'line': None,
        'name': 'ValueError',
        'step': 'step6',
        'swallowed': False,
    }

    # 1 & 2 don't run,
    # 3 runs, no error
    # 4 runs, error and swallows
    # 5 skips
    # 6 runs, error and raises
    # 7 doesn't run because execution stopped at 6 because of error
    mock_invoke_step.side_effect = [
        None,  # 3
        step4_run_error_swallow['exception'],  # 4
        step6_run_error_raise['exception'],  # 6
    ]

    steps = [
        Step.from_step_definition({
            'name': 'step1',
            'run': False
        }),
        Step.from_step_definition({
            'name': 'step2',
            'skip': True
        }),
        Step.from_step_definition({
            'name': 'step3',
        }),
        Step.from_step_definition({
            'name': 'step4',
            'run': True,
            'skip': False,
            'swallow': 1
        }),
        Step.from_step_definition({
            'name': 'step5',
            'run': True,
            'skip': True,
            'swallow': True
        }),
        Step.from_step_definition('step6'),
        Step.from_step_definition('step7'),
    ]

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
            with pytest.raises(ValueError) as err_info:
                PipelineBody.from_mapping({}).run_pipeline_steps(
                    steps,
                    context)

                assert str(err_info.value) == "arb error here 6"

    assert mock_logger_info.call_args_list == [
        call('step1 not running because run is False.'),
        call('step2 not running because skip is True.'),
        call('step5 not running because skip is True.')]

    assert mock_invoke_step.call_count == 3

    assert mock_logger_error.call_args_list == [
        call(
            "step4 Ignoring error because swallow is True "
            "for this step.\n"
            "ValueError: arb error here 4"
        ),
        call("Error while running step step6"),
    ]

    assert mock_invoke_step.call_count == 3

    # step3
    assert mock_invoke_step.call_args_list[0] == call(
        context=get_test_context()
    )

    # step4
    assert mock_invoke_step.call_args_list[1] == call(
        context=get_test_context()
    )

    step6_context = mock_invoke_step.call_args_list[2][1]["context"]
    assert get_test_context().items() <= step6_context.items()
    assert len(step6_context['runErrors']) == 1

    # validate all the in params ended up in context as intended,
    # plus runErrors
    assert len(context) == original_len + 1
    assert len(context['runErrors']) == 2

    assert step4_run_error_swallow == context['runErrors'][0]
    assert step6_run_error_raise == context['runErrors'][1]

# endregion run_pipeline_steps: swallow


# endregion run_pipeline_steps

# region run_step_group

@patch.object(PipelineBody, 'run_pipeline_steps')
def test_run_step_group_pass(mock_run_steps):
    """run_step_group gets and runs steps for group."""
    PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_group(
        step_group_name='sg1',
        context=Context())

    mock_run_steps.assert_called_once_with(steps=[
        Step('step1'),
        Step('step2'),
        Step('step3key1',
             in_parameters={'in3k1_1': 'v3k1', 'in3k1_2': 'v3k2'}),
        Step('step4')
    ], context={})


@patch.object(PipelineBody, 'run_pipeline_steps')
def test_run_step_group_no_raise(mock_run_steps):
    """run_step_group with raise_stop False."""
    mock_run_steps.side_effect = StopStepGroup()
    PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_group(
        step_group_name='sg1',
        context=Context(),
        raise_stop=False)

    mock_run_steps.assert_called_once_with(steps=[
        Step('step1'),
        Step('step2'),
        Step('step3key1',
             in_parameters={'in3k1_1': 'v3k1', 'in3k1_2': 'v3k2'}),
        Step('step4')
    ], context={})


@patch.object(PipelineBody, 'run_pipeline_steps')
def test_run_step_group_raise(mock_run_steps):
    """run_step_group with raise_stop True."""
    mock_run_steps.side_effect = StopStepGroup()
    with pytest.raises(StopStepGroup):
        PipelineBody.from_mapping(
            get_valid_test_pipeline()).run_step_group(
                                              step_group_name='sg1',
                                              context=Context(),
                                              raise_stop=True)

    mock_run_steps.assert_called_once_with(steps=[
        Step('step1'),
        Step('step2'),
        Step('step3key1',
             in_parameters={'in3k1_1': 'v3k1', 'in3k1_2': 'v3k2'}),
        Step('step4')
    ], context={})

# endregion run_step_group

# region run_step_groups


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_single(mock_run_step_group):
    """Single test group runs with success."""
    PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
        groups=['sg1'],
        success_group='arb success',
        failure_group='arb fail',
        context=Context())

    assert mock_run_step_group.mock_calls == [call('sg1', context={}),
                                              call('arb success', context={})]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_single_no_success_handler(mock_run_step_group):
    """Single test group runs with no success handler."""
    PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
        groups=['sg1'],
        success_group=None,
        failure_group='arb fail',
        context=Context())

    assert mock_run_step_group.mock_calls == [call('sg1', context={})]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence(mock_run_step_group):
    """Sequence of test groups runs with success."""
    PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
        groups=['sg3', 'sg1', 'sg2', 'sg4'],
        success_group='arb success',
        failure_group='arb fail',
        context=Context())

    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={}),
                                              call('sg4', context={}),
                                              call('arb success', context={})]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence_with_fail(mock_run_step_group):
    """Sequence of test groups runs with failure."""
    mock_run_step_group.side_effect = [None, None, ValueError('arb')]

    with pytest.raises(ValueError) as err:
        PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
            groups=['sg3', 'sg1', 'sg2', 'sg4'],
            success_group='arb success',
            failure_group='arb fail',
            context=Context())

    assert str(err.value) == 'arb'
    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={}),
                                              call('arb fail',
                                                   context={},
                                                   raise_stop=True)
                                              ]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence_with_failing_fail(mock_run_step_group):
    """Sequence of test groups runs with failure, failure handler fails."""
    mock_run_step_group.side_effect = [None,
                                       None,
                                       ValueError('arb'),
                                       KeyError('arb failure handler err')]

    with pytest.raises(ValueError) as err:
        PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
            groups=['sg3', 'sg1', 'sg2', 'sg4'],
            success_group='arb success',
            failure_group='arb fail',
            context=Context())

    # failure handler swallows arb KeyError
    assert str(err.value) == 'arb'
    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={}),
                                              call('arb fail',
                                                   context={},
                                                   raise_stop=True)
                                              ]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence_with_failing_stop(
        mock_run_step_group):
    """Groups run with failure, failure handler Stop."""
    mock_run_step_group.side_effect = [None,
                                       None,
                                       ValueError('arb'),
                                       Stop]

    with pytest.raises(Stop):
        PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
            groups=['sg3', 'sg1', 'sg2', 'sg4'],
            success_group='arb success',
            failure_group='arb fail',
            context=Context())

    # failure handler swallows arb KeyError
    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={}),
                                              call('arb fail',
                                                   context={},
                                                   raise_stop=True)
                                              ]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence_with_failing_stoppipeline(
        mock_run_step_group):
    """Groups run with failure, failure handler StopPipeline."""
    mock_run_step_group.side_effect = [None,
                                       None,
                                       ValueError('arb'),
                                       StopPipeline]

    with pytest.raises(StopPipeline):
        PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
            groups=['sg3', 'sg1', 'sg2', 'sg4'],
            success_group='arb success',
            failure_group='arb fail',
            context=Context())

    # failure handler swallows arb KeyError
    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={}),
                                              call('arb fail',
                                                   context={},
                                                   raise_stop=True)
                                              ]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence_with_failing_stopstepgroup(
        mock_run_step_group):
    """Test groups runs with failure, failure handler raises StopStepGroup."""
    mock_run_step_group.side_effect = [None,
                                       None,
                                       ValueError('arb'),
                                       StopStepGroup]

    PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
        groups=['sg3', 'sg1', 'sg2', 'sg4'],
        success_group='arb success',
        failure_group='arb fail',
        context=Context())

    # failure handler swallows arb ValueError
    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={}),
                                              call('arb fail',
                                                   context={},
                                                   raise_stop=True)
                                              ]


@patch.object(PipelineBody, 'run_step_group')
def test_run_step_groups_sequence_with_fail_no_handler(mock_run_step_group):
    """Sequence of test groups runs with failure when no failure handler."""
    mock_run_step_group.side_effect = [None, None, ValueError('arb')]

    with pytest.raises(ValueError) as err:
        PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
            groups=['sg3', 'sg1', 'sg2', 'sg4'],
            success_group='arb success',
            failure_group=None,
            context=Context())

    assert str(err.value) == 'arb'
    assert mock_run_step_group.mock_calls == [call('sg3', context={}),
                                              call('sg1', context={}),
                                              call('sg2', context={})]


def test_run_step_groups_sequence_with_mutate():
    """Sequence of test groups runs with success and mutates context."""
    context = Context({'counter': 5})
    PipelineBody.from_mapping(get_valid_steps_pipeline()).run_step_groups(
        groups=['sg3', 'sg1', 'sg2', 'sg4'],
        success_group='arb success',
        failure_group='arb fail',
        context=context)

    assert context['counter'] == 8


def test_run_step_groups_none_groups():
    """Raise error if groups None."""
    with pytest.raises(ValueError) as err:
        PipelineBody.from_mapping(get_valid_test_pipeline()).run_step_groups(
            groups=None,
            success_group='arb success',
            failure_group='arb fail',
            context=Context())

    assert str(err.value) == (
        'you must specify which step-groups you want to run. groups is None.')
# endregion run_step_groups

# region Jump


def get_jump_pipeline():
    """Test pipeline for jump."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


def nothing_step(context):
    """Do nothing."""
    pass


def jump_step(groups, success=None, failure=None):
    """Jump step mock."""
    def run_step(context):
        raise Jump(groups, success, failure, 'jumparb')
    return run_step


def call_step(groups,
              success=None,
              failure=None,
              original_config=('call', 'arb')):
    """Call step mock."""
    def run_step(context):
        raise Call(groups, success, failure, original_config)
    return run_step

class StepStubs():
    """Stubs for fake steps. It maps the step-name into mock on run_step."""
    def __init__(self):
        """Initialize mock to record stubs calls"""
        self.mock = Mock()

    def nothing_step(self, context):
        """Do nothing."""
        pass


    def jump_step(self, groups, success=None, failure=None):
        """Jump step mock."""
        def run_step(context):
            raise Jump(groups, success, failure, 'jumparb')
        return run_step


    def call_step(self,
                  groups,
                  success=None,
                  failure=None,
                  original_config=('call', 'arb')):
        """Call step mock."""
        def run_step(context):
            raise Call(groups, success, failure, original_config)
        return run_step

    def unmapped(self, context):
        """Throw deliberate error if trying to use a step that was unexpected."""
        raise ValueError("step_name wasn't found in fake cache.")

    def fake_step_cache(self, step_to_func_mapping):
        """Initialize step-name to stub mapping like the pypyr cache does."""
        def get_step(step_name):
            def _run_me(context):
                self.mock(step_name)
                step_to_func_mapping.get(step_name, self.unmapped)(context)
            return _run_me
        return get_step


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_jump_with_success_handler(mock_step_cache):
    """Jump between different step groups with success handler."""
    # Sequence: sg2 - sg2.1 (JUMP)
    #           sg1 - sg1.1, sg 1.2 (JUMP)
    #           sg4 - sg4.1 (JUMP)
    #           sg3 - sg3.1, sg 3.2
    #           sg5 - sg5.1 (on_success)
    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': stubs.jump_step(['sg1']),
        'sg1.step1': stubs.nothing_step,
        'sg1.step2': stubs.jump_step(['sg4']),  
        'sg4.step1': stubs.jump_step(['sg3']),
        'sg3.step1': stubs.nothing_step,
        'sg3.step2': stubs.nothing_step,
        'sg5.step1': stubs.nothing_step,
    })

    context = Context()
    PipelineBody.from_mapping(get_jump_pipeline()).run_step_groups(
        groups=['sg2'],
        success_group='sg5',
        failure_group=None,
        context=context)

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg5.step1')]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_jump_with_failure_handler(mock_step_cache):
    """Jump between different step groups with failure handler."""
    # Sequence: sg2 - sg2.1 (JUMP)
    #           sg3 - sg3.1 (ERROR)
    #           sg4 - sg4.1, sg4.2 (failure handler)
    def err_step(context):
        raise ValueError('3.1')

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': stubs.jump_step(['sg3']),  # 2.1
        'sg3.step1': err_step,  # 3.1
        'sg4.step1': stubs.nothing_step,  # 4.1
        'sg4.step2': stubs.nothing_step,  # 4.2
    })

    context = Context()
    with pytest.raises(ValueError) as err_info:
        PipelineBody.from_mapping(get_jump_pipeline()).run_step_groups(
            groups=['sg2', 'sg1'],
            success_group='sg5',
            failure_group='sg4',
            context=context)

    assert str(err_info.value) == '3.1'
    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg3.step1'),
                                     call('sg4.step1'),
                                     call('sg4.step2')]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_jump_with_group_sequences_and_success_jump(mock_step_cache):
    """Jump between step groups with success handler and jump in success."""
    # Sequence: sg2 - sg2.1, sg2.2
    #           sg1 - sg1.1, sg 1.2 (JUMP)
    #           sg4 - sg4.1, sg 4.2
    #           sg3 - sg3.1, sg 3.2
    #           sg6 - sg6.1 (JUMP) - on_success
    #           sg5 - sg5.1

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': nothing_step,  # 2.1
        'sg2.step2': nothing_step,  # 2.2
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': jump_step(['sg4', 'sg3']),  # 1.2
        'sg4.step1': nothing_step,  # 4.1
        'sg4.step2': nothing_step,  # 4.2
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
        'sg6.step1': jump_step(['sg5']),  # 6.1
        'sg5.step1': nothing_step,  # 5.1
        'sg5.step2': nothing_step,  # 5.2
    })

    context = Context()
    PipelineBody.from_mapping(get_jump_pipeline()).run_step_groups(
        groups=['sg2', 'sg1'],
        success_group='sg6',
        failure_group=None,
        context=context)

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step2'),
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg4.step2'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg6.step1'),
                                     call('sg5.step1')]


def get_while_pipeline():
    """Test pipeline for while."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            {'name': 'sg2.step1',
             'while': {
                 'max': 3}
             },
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_jump_with_while(mock_step_cache):
    """Jump between different step groups in a while."""
    # Sequence: sg2 - sg2.1 x2 (JUMP)
    #           sg1 - sg1.1, sg 1.2 (JUMP)
    #           sg4 - sg4.1 (JUMP)
    #           sg3 - sg3.1, sg 3.2
    #           sg5 - sg5.1 (on_success)

    mock21 = DeepCopyMagicMock()

    def step21(context):
        mock21(context)
        if context['whileCounter'] == 2:
            jump_step(['sg1'])(context)

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': step21,  # 2.1
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': jump_step(['sg4']),  # 1.2
        'sg4.step1': jump_step(['sg3']),  # 4.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
        'sg5.step1': nothing_step,  # 5.1
    })

    context = Context({'a': 'b'})
    PipelineBody.from_mapping(get_while_pipeline()).run_step_groups(
        groups=['sg2'],
        success_group='sg5',
        failure_group=None,
        context=context)

    assert mock21.mock_calls == [call({'a': 'b', 'whileCounter': 1}),
                                 call({'a': 'b', 'whileCounter': 2})]

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step1'), # repeats coz while
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg5.step1')]

    assert context == {'a': 'b', 'whileCounter': 2}


def get_for_pipeline():
    """Test pipeline for for."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            {'name': 'sg2.step1',
             'foreach': ['one', 'two', 'three']
             },
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_jump_with_for(mock_step_cache):
    """Jump between different step groups in a foreach."""
    # Sequence: sg2 - sg2.1 x2 (JUMP)
    #           sg1 - sg1.1, sg 1.2 (JUMP)
    #           sg4 - sg4.1 (JUMP)
    #           sg3 - sg3.1, sg 3.2
    #           sg5 - sg5.1 (on_success)

    mock21 = DeepCopyMagicMock()

    def step21(context):
        mock21(context)
        if context['i'] == 'two':
            jump_step(['sg1'])(context)

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': step21,  # 2.1
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': jump_step(['sg4']),  # 1.2
        'sg4.step1': jump_step(['sg3']),  # 4.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
        'sg5.step1': nothing_step,  # 5.1
    })

    context = Context({'a': 'b'})
    PipelineBody.from_mapping(get_for_pipeline()).run_step_groups(
        groups=['sg2'],
        success_group='sg5',
        failure_group=None,
        context=context)

    assert mock21.mock_calls == [call({'a': 'b', 'i': 'one'}),
                                 call({'a': 'b', 'i': 'two'})]
    

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step1'), # repeats coz for
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg5.step1')]

    assert context == {'a': 'b', 'i': 'two'}
# endregion Jump


# region StopStepGroup
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_step_group_with_success_handler(mock_step_cache):
    """Stop step group with success handler."""
    # Sequence: sg2 - sg2.1, sg2.2
    #           sg1 - sg1.1 STOP
    #           sg3 - sg3.1, sg3.2 - success handler
    def stop_step_group_step(context):
        raise StopStepGroup()

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': nothing_step,  # 2.1
        'sg2.step2': nothing_step,  # 2.2
        'sg1.step1': stop_step_group_step,  # 1.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
    })

    context = Context()
    PipelineBody.from_mapping(get_jump_pipeline()).run_step_groups(
        groups=['sg2', 'sg1'],
        success_group='sg3',
        failure_group=None,
        context=context)

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step2'),
                                     call('sg1.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2')
                                    ]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_step_group_with_jumps(mock_step_cache):
    """Stop Step Group with jumps."""
    # Sequence: sg2 - sg2.1 (JUMP)
    #           sg1 - sg1.1, sg 1.2 - STOP
    def stop_step_group_step(context):
        raise StopStepGroup()

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': jump_step(['sg1']),  # 2.1
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': stop_step_group_step  # 1.2
    })

    context = Context()
    PipelineBody.from_mapping(get_jump_pipeline()).run_step_groups(
        groups=['sg2'],
        success_group=None,
        failure_group=None,
        context=context)

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg1.step1'),
                                     call('sg1.step2')]


def get_for_11_pipeline():
    """Test pipeline for for."""
    return {
        'sg1': [
            {'name': 'sg1.step1',
             'foreach': ['one', 'two', 'three']
             },
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_step_group_with_success_handler_for(mock_step_cache):
    """Stop step group with success handler in for loop."""
    # Sequence: sg2 - sg2.1, sg2.2
    #           sg1 - sg1.1 x2 STOP
    #           sg3 - sg3.1, sg3.2 - success handler
    mock11 = DeepCopyMagicMock()

    def step11(context):
        mock11(context)
        if context['i'] == 'two':
            raise StopStepGroup()

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': nothing_step,  # 2.1
        'sg2.step2': nothing_step,  # 2.2
        'sg1.step1': step11,  # 1.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
    })

    context = Context({'a': 'b'})
    PipelineBody.from_mapping(get_for_11_pipeline()).run_step_groups(
        groups=['sg2', 'sg1'],
        success_group='sg3',
        failure_group=None,
        context=context)

    assert mock11.mock_calls == [call({'a': 'b', 'i': 'one'}),
                                 call({'a': 'b', 'i': 'two'})]
    assert context == {'a': 'b', 'i': 'two'}

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step2'),
                                     call('sg1.step1'),
                                     call('sg1.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2')
                                    ]


def get_while_11_pipeline():
    """Test pipeline for while."""
    return {
        'sg1': [
            {'name': 'sg1.step1',
             'while': {
                 'max': 3}
             },
            'sg1.step2'
        ],
        'sg2': [
            'sg2.step1',
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_stop_step_group_with_success_handler_while(mock_step_cache):
    """Stop step group with success handler in while loop."""
    # Sequence: sg2 - sg2.1, sg2.2
    #           sg1 - sg1.1 x2 STOP
    #           sg3 - sg3.1, sg3.2 - success handler
    mock11 = DeepCopyMagicMock()

    def step11(context):
        mock11(context)
        if context['whileCounter'] == 2:
            raise StopStepGroup()

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': nothing_step,  # 2.1
        'sg2.step2': nothing_step,  # 2.2
        'sg1.step1': step11,  # 1.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
    })

    context = Context({'a': 'b'})
    PipelineBody.from_mapping(get_while_11_pipeline()).run_step_groups(
        groups=['sg2', 'sg1'],
        success_group='sg3',
        failure_group=None,
        context=context)

    assert mock11.mock_calls == [call({'a': 'b', 'whileCounter': 1}),
                                 call({'a': 'b', 'whileCounter': 2})]
    assert context == {'a': 'b', 'whileCounter': 2}

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step2'),
                                     call('sg1.step1'),
                                     call('sg1.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2')
                                    ]
# endregion StopStepGroup


# region Call
@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_call_with_success_handler(mock_step_cache):
    """Call between different step groups with success handler."""
    # Sequence: sg2 - sg2.1 (CALL)
    #           sg1 - sg1.1, sg 1.2 (CALL)
    #           sg4 - sg4.1 (CALL)
    #           sg3 - sg3.1, sg 3.2
    #           sg 4.2, sg2.2 (come back to call point)
    #           sg5 - sg5.1 (on_success)

    stubs = StepStubs()

    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': call_step(['sg1']),  # 2.1
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': call_step(['sg4']),  # 1.2
        'sg4.step1': call_step(['sg3']),  # 4.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
        'sg4.step2': nothing_step,  # 4.2
        'sg2.step2': nothing_step,  # 2.2
        'sg5.step1': nothing_step,  # 5.1
    })

    context = Context({'call': {'groups': 'sg1'}})

    pipeline = Pipeline('arb')
    pipeline_body = PipelineBody.from_mapping(get_jump_pipeline())
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=pipeline_body,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))
    
    with context.pipeline_scope(pipeline):
        pipeline_body.run_step_groups(
            groups=['sg2'],
            success_group='sg5',
            failure_group=None,
            context=context)

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg4.step2'),
                                     call('sg2.step2'),
                                     call('sg5.step1')]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_call_with_failure_handler(mock_step_cache):
    """Call between different step groups with failure handler."""
    # Sequence: sg2 - sg2.1 (CALL)
    #           sg3 - sg3.1 (ERROR)
    #           sg4 - sg4.1, sg4.2 (failure handler)
    def err_step(context):
        raise ValueError('3.1')


    stubs = StepStubs()
    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': call_step(['sg3']),  # 2.1
        'sg3.step1': err_step,  # 3.1
        'sg4.step1': nothing_step,  # 4.1
        'sg4.step2': nothing_step,  # 4.2
    })

    context = Context({'call': {'groups': 'sg3'}})

    pipeline = Pipeline('arb')
    pipeline_body = PipelineBody.from_mapping(get_jump_pipeline())
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=pipeline_body,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))
    
    with context.pipeline_scope(pipeline):
        with pytest.raises(ValueError) as err_info:
            pipeline_body.run_step_groups(
                groups=['sg2', 'sg1'],
                success_group='sg5',
                failure_group='sg4',
                context=context)

    assert str(err_info.value) == '3.1'
    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg3.step1'),
                                     call('sg4.step1'),
                                     call('sg4.step2')]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_call_with_failure_handler_while(mock_step_cache):
    """Call between different step groups with failure handler."""
    # Sequence: sg2 - sg2.1 x2 (CALL)
    #           sg3 - sg3.1 (ERROR)
    #           sg4 - sg4.1, sg4.2 (failure handler)
    def err_step(context):
        raise ValueError('3.1')

    mock21 = DeepCopyMagicMock()

    def step21(context):
        mock21(context)
        if context['whileCounter'] == 2:
            context['call'] = "step21"
            call_step(['sg3'])(context)

    stubs = StepStubs()
    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': step21,  # 2.1
        'sg3.step1': err_step,  # 3.1
        'sg4.step1': nothing_step,  # 4.1
        'sg4.step2': nothing_step,  # 4.2
    })

    context = Context({'a': 'b'})

    pipeline = Pipeline('arb')
    pipeline_body = PipelineBody.from_mapping(get_while_pipeline())
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=pipeline_body,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))

    with context.pipeline_scope(pipeline):
        with pytest.raises(ValueError) as err_info:
            pipeline_body.run_step_groups(
                groups=['sg2', 'sg1'],
                success_group='sg5',
                failure_group='sg4',
                context=context)

    assert str(err_info.value) == '3.1'
    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step1'), # 2x coz while
                                     call('sg3.step1'),
                                     call('sg4.step1'),
                                     call('sg4.step2')]

    assert mock21.mock_calls == [call({'a': 'b',
                                       'whileCounter': 1
                                       }),
                                 call({'a': 'b',
                                       'whileCounter': 2
                                       })]

    assert repr(context) == repr({'a': 'b',
                                  'whileCounter': 2,
                                  'call': 'arb',
                                  'runErrors': [
                                      {'name': 'ValueError',
                                       'description': '3.1',
                                       'customError': {},
                                       'line': None,
                                       'col': None,
                                       'step': 'sg3.step1',
                                       'exception': ValueError('3.1'),
                                       'swallowed': False}
                                  ]})


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_call_with_no_failure_handler(mock_step_cache):
    """Call between different step groups raising an error and no handler."""
    # Sequence: sg2 - sg2.1 (CALL)
    #           sg3 - sg3.1 (ERROR)
    #           sg4 - sg4.1, sg4.2 (failure handler)
    def err_step(context):
        raise ValueError('3.1')

    stubs = StepStubs()
    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': call_step(['sg3']),  # 2.1
        'sg3.step1': err_step,  # 3.1
        'sg4.step1': nothing_step,  # 4.1
        'sg4.step2': nothing_step,  # 4.2
    })

    context = Context({'call': {'groups': 'sg3'}})

    pipeline = Pipeline('arb')
    pipeline_body = PipelineBody.from_mapping(get_jump_pipeline())
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=pipeline_body,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))

    with context.pipeline_scope(pipeline):
        with pytest.raises(ValueError) as err_info:
            pipeline_body.run_step_groups(
                groups=['sg2', 'sg1'],
                success_group=None,
                failure_group=None,
                context=context)

    assert str(err_info.value) == '3.1'
    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg3.step1')]


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_call_with_success_handler_for(mock_step_cache):
    """Call between different step groups with success handler in for."""
    # Sequence: sg2 - sg2.1 x2 (CALL)
    #           sg1 - sg1.1, sg 1.2 (CALL)
    #           sg4 - sg4.1 (CALL)
    #           sg3 - sg3.1, sg 3.2
    #           sg 4.2, (come back to call point)
    #           sg2.1 x1 (back in for iterator)
    #           sg2.2 (complete sg2)
    #           sg5 - sg5.1 (on_success)
    mock21 = DeepCopyMagicMock()

    def step21(context):
        mock21(context)
        if context['i'] == 'two':
            context['call'] = 'sg1'
            call_step(['sg1'])(context)

    def mutate_step(context):
        context['a'] = 'changed'

    def mutate_after_loop(context):
        context['a'] = 'after loop'

    stubs = StepStubs()
    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': step21,  # 2.1
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': call_step(['sg4']),  # 1.2
        'sg4.step1': call_step(['sg3']),  # 4.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
        'sg4.step2': mutate_step,  # 4.2
        'sg2.step2': mutate_after_loop,  # 2.2
        'sg5.step1': nothing_step,  # 5.1
    })

    context = Context({'a': 'b'})

    pipeline = Pipeline('arb')
    pipeline_body = PipelineBody.from_mapping(get_for_pipeline())
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=pipeline_body,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))
    
    with context.pipeline_scope(pipeline):
        pipeline_body.run_step_groups(
            groups=['sg2'],
            success_group='sg5',
            failure_group=None,
            context=context)

    assert mock21.mock_calls == [call({'a': 'b',
                                       'i': 'one'}),
                                 call({'a': 'b',
                                       'i': 'two'}),
                                 call({'a': 'changed',
                                       'i': 'three',
                                       'call': 'arb'})]
    assert context == {'a': 'after loop', 'i': 'three', 'call': 'arb'}

    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step1'), # 2x for
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg4.step2'),
                                     call('sg2.step1'),
                                     call('sg2.step2'), # complete for
                                     call('sg5.step1')]


def get_retry_pipeline():
    """Test pipeline for retry."""
    return {
        'sg1': [
            'sg1.step1',
            'sg1.step2'
        ],
        'sg2': [
            {'name': 'sg2.step1',
             'retry': {
                 'max': 3}
             },
            'sg2.step2'
        ],
        'sg3': [
            'sg3.step1',
            'sg3.step2'
        ],
        'sg4': [
            'sg4.step1',
            'sg4.step2'
        ],
        'sg5': [
            'sg5.step1'
        ],
        'sg6': [
            'sg6.step1',
            'sg6.step2'
        ]
    }


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_call_with_success_handler_retry(mock_step_cache):
    """Call between different step groups with success handler in retry."""
    # Sequence: sg2 - sg2.1 x2 (CALL)
    #           sg1 - sg1.1, sg 1.2 (CALL)
    #           sg4 - sg4.1 (CALL)
    #           sg3 - sg3.1, sg 3.2
    #           sg 4.2, sg2.2 (come back to call point)
    #           sg5 - sg5.1 (on_success)
    mock21 = DeepCopyMagicMock()

    def step21(context):
        mock21(context)
        if context['retryCounter'] == 2:
            context['call'] = 'sg1'
            call_step(['sg1'])(context)
        else:
            raise ValueError(context['retryCounter'])

    stubs = StepStubs()
    mock_step_cache.side_effect = stubs.fake_step_cache({
        'sg2.step1': step21,  # 2.1
        'sg1.step1': nothing_step,  # 1.1
        'sg1.step2': call_step(['sg4']),  # 1.2
        'sg4.step1': call_step(['sg3']),  # 4.1
        'sg3.step1': nothing_step,  # 3.1
        'sg3.step2': nothing_step,  # 3.2
        'sg4.step2': nothing_step,  # 4.2
        'sg2.step2': nothing_step,  # 2.2
        'sg5.step1': nothing_step,  # 5.1
    })

    context = Context({'a': 'b'})

    pipeline = Pipeline('arb')
    pipeline_body = PipelineBody.from_mapping(get_retry_pipeline())
    pipeline.pipeline_definition = PipelineDefinition(
        pipeline=pipeline_body,
        info=PipelineInfo(pipeline_name='arb',
                          loader=None,
                          parent=None))
    
    with context.pipeline_scope(pipeline):
        pipeline_body.run_step_groups(
            groups=['sg2'],
            success_group='sg5',
            failure_group=None,
            context=context)

    assert mock21.mock_calls == [call({'a': 'b',
                                       'retryCounter': 1}),
                                 call({'a': 'b',
                                       'retryCounter': 2})]
    assert context == {'a': 'b',
                       'retryCounter': 2,
                       'call': 'arb'}
    assert stubs.mock.mock_calls == [call('sg2.step1'),
                                     call('sg2.step1'), # 2x retry
                                     call('sg1.step1'),
                                     call('sg1.step2'),
                                     call('sg4.step1'),
                                     call('sg3.step1'),
                                     call('sg3.step2'),
                                     call('sg4.step2'),
                                     call('sg2.step2'),
                                     call('sg5.step1')]

# endregion Call
