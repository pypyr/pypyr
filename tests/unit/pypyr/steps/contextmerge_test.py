"""contextmerge.py unit tests."""
import logging
import pytest
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.contextmerge
from tests.common.utils import patch_logger


def test_contextmerge_throws_on_empty_context():
    """Input context must exist."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.contextmerge.run_step(Context())


def test_contextmerge_throws_on_contextset_missing():
    """Input contextMerge must exist in context."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.contextmerge.run_step(Context({'arbkey': 'arbvalue'}))

    assert str(err_info.value) == ("context['contextMerge'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.contextmerge.")


def test_contextmerge_pass_no_substitutions():
    """Input contextmerge success case with no substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'contextMerge': {
            'key2': 'value4',
            'key4': 'value5'
        }
    })

    pypyr.steps.contextmerge.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value4'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value5'


def test_contextmerge_pass_different_types_with_log():
    """Input contextmerge success case with substitutions of non strings."""
    context = Context({
        'k1': 33,
        'k2': 123.45,
        'k3': False,
        'contextMerge': {
            'kint': '{k1}',
            'kfloat': '{k2}',
            'kbool': '{k3}'
        }
    })

    with patch_logger(
            'pypyr.steps.contextmerge', logging.INFO) as mock_logger_info:
        pypyr.steps.contextmerge.run_step(context)

    mock_logger_info.assert_called_once_with('merged 3 context items.')

    assert context['kint'] == 33
    assert context['k1'] == 33
    assert context['kfloat'] == 123.45
    assert context['k2'] == 123.45
    assert not context['kbool']
    assert isinstance(context['kbool'], bool)
    assert not context['k3']


def test_contextmerge_list():
    """Simple list."""
    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'ctx4': [1, 2, 3],
                       'contextMerge': {
                           'ctx4': ['k1', 'k2', '{ctx3}', True, False, 44]
                       }})

    pypyr.steps.contextmerge.run_step(context)

    assert context['ctx1'] == 'ctxvalue1'
    assert context['ctx2'] == 'ctxvalue2'
    assert context['ctx3'] == 'ctxvalue3'
    output = context['ctx4']
    assert len(output) == 9
    assert output[0] == 1
    assert output[1] == 2
    assert output[2] == 3
    assert output[3] == 'k1'
    assert output[4] == 'k2'
    assert output[5] == 'ctxvalue3'
    assert output[6]
    assert not output[7]
    assert output[8] == 44


def test_contextmerge_list_additive():
    """Simple list additive."""
    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'ctx4': [1, 2, 3],
                       'contextMerge': {
                           'ctx4': [44]
                       }})

    pypyr.steps.contextmerge.run_step(context)

    output = context['ctx4']
    assert len(output) == 4
    assert output[0] == 1
    assert output[1] == 2
    assert output[2] == 3
    assert output[3] == 44


def test_get_formatted_iterable_nested_with_formatting_merge():
    """Straight deepish copy with formatting on merge."""
    # dict containing dict, list, dict-list-dict, tuple, dict-tuple-list, bytes
    input_obj = {'k1': 'v1',
                 'k2': 'v2_{ctx1}',
                 'k3': bytes('v3{ctx1}', encoding='utf-8'),
                 'k4': [
                     1,
                     2,
                     '3_{ctx4}here',
                     {'key4.1': 'value4.1',
                      '{ctx2}_key4.2': 'value_{ctx3}_4.2',
                      'key4.3': {
                          '4.3.1': '4.3.1value',
                          '4.3.2': '4.3.2_{ctx1}_value'}}
                 ],
                 'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                 'k6': ('six6.1', False, [0, 1, 2], 77, 'six_{ctx1}_end'),
                 'k7': 'simple string to close 7'
                 }

    context = Context(
        {'ctx1': 'ctxvalue1',
         'ctx2': 'ctxvalue2',
         'ctx3': 'ctxvalue3',
         'ctx4': 'ctxvalue4',
         'output': {
             'ok1': 'ov1',
             'ok2': 'ov2_{ctx2}',
             'ok3': bytes('ov3{ctx1}', encoding='utf-8'),
             'ok4': [
                 3,
                 4,
                 'o3_{ctx4}here',
                 {'okey4.1': 'ovalue4.1',
                  'o_{ctx2}_key4.2': 'o_value_{ctx3}_4.2',
                  'o_key4.3': {
                      'o_4.3.1': 'o_4.3.1value',
                      'o_4.3.2': 'o_4.3.2_{ctx1}_value'}}
             ]
         },
         'contextMerge': {
             'output': input_obj}})

    pypyr.steps.contextmerge.run_step(context)

    output = context['output']

    # context values outside of merge key remain unmolested
    assert context['ctx1'] == 'ctxvalue1'
    assert context['ctx2'] == 'ctxvalue2'
    assert context['ctx3'] == 'ctxvalue3'
    assert context['ctx4'] == 'ctxvalue4'
    assert context['contextMerge'] == {'output': input_obj}

    # mergey key not the same as the original anymore since new items merged in
    assert output != input_obj

    # original keys/values in merge key remain unmolested since they weren't
    # merge targets
    assert output['ok1'] == 'ov1'
    assert output['ok2'] == 'ov2_{ctx2}'
    assert output['ok3'] == b'ov3{ctx1}'
    assert output['ok4'] == [
        3,
        4,
        'o3_{ctx4}here',
        {'okey4.1': 'ovalue4.1',
         'o_{ctx2}_key4.2': 'o_value_{ctx3}_4.2',
         'o_key4.3': {
             'o_4.3.1': 'o_4.3.1value',
             'o_4.3.2': 'o_4.3.2_{ctx1}_value'}}
    ]

    # verify formatted strings that were merged
    assert input_obj['k2'] == 'v2_{ctx1}'
    assert output['k2'] == 'v2_ctxvalue1'

    assert input_obj['k3'] == b'v3{ctx1}'
    assert output['k3'] == b'v3{ctx1}'

    assert input_obj['k4'][2] == '3_{ctx4}here'
    assert output['k4'][2] == '3_ctxvalue4here'

    assert input_obj['k4'][3]['{ctx2}_key4.2'] == 'value_{ctx3}_4.2'
    assert output['k4'][3]['ctxvalue2_key4.2'] == 'value_ctxvalue3_4.2'

    assert input_obj['k4'][3]['key4.3']['4.3.2'] == '4.3.2_{ctx1}_value'
    assert output['k4'][3]['key4.3']['4.3.2'] == '4.3.2_ctxvalue1_value'

    assert input_obj['k6'][4] == 'six_{ctx1}_end'
    assert output['k6'][4] == 'six_ctxvalue1_end'

    # verify this was a deep copy - obj refs has to be different for nested
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][3]['key4.3']) != id(input_obj['k4'][3]['key4.3'])
    assert id(output['k5']) != id(input_obj['k5'])
    assert id(output['k6']) != id(input_obj['k6'])
    assert id(output['k6'][2]) != id(input_obj['k6'][2])
    # strings are interned in python, so id is the same
    assert id(output['k7']) == id(input_obj['k7'])
    output['k7'] = 'mutate 7 on new'
    assert input_obj['k7'] == 'simple string to close 7'
    assert output['k7'] == 'mutate 7 on new'
