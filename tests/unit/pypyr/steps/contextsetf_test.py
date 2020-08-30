"""contextsetf.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.contextsetf
import pytest


def test_contextsetf_throws_on_empty_context():
    """Context must exist."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.contextsetf.run_step(Context())


def test_contextsetf_throws_on_contextset_missing():
    """Input contextSetf must exist in context."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.contextsetf.run_step(Context({'arbkey': 'arbvalue'}))

    assert str(err_info.value) == ("context['contextSetf'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.contextsetf.")


def test_contextsetf_pass_no_substitutions():
    """Input contextsetf success case with no substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'contextSetf': {
            'key2': 'value4',
            'key4': 'value5'
        }
    })

    pypyr.steps.contextsetf.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value4'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value5'


def test_contextsetf_pass_substitutions():
    """Input contextsetf success case with substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'contextSetf': {
            'key2': '{key1}',
            'key4': '{key3}'
        }
    })

    pypyr.steps.contextsetf.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value1'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value3'


def test_contextsetf_pass_different_types():
    """Input contextsetf success case with substitutions of non strings."""
    context = Context({
        'k1': 33,
        'k2': 123.45,
        'k3': False,
        'contextSetf': {
            'kint': '{k1}',
            'kfloat': '{k2}',
            'kbool': '{k3}'
        }
    })

    pypyr.steps.contextsetf.run_step(context)

    assert context['kint'] == 33
    assert context['k1'] == 33
    assert context['kfloat'] == 123.45
    assert context['k2'] == 123.45
    assert not context['kbool']
    assert isinstance(context['kbool'], bool)
    assert not context['k3']


def test_contextsetf_list():
    """Simple list."""
    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'contextSetf': {
                           'output': ['k1', 'k2', '{ctx3}', True, False, 44]
                       }})

    pypyr.steps.contextsetf.run_step(context)

    output = context['output']
    assert output[0] == 'k1'
    assert output[1] == 'k2'
    assert output[2] == 'ctxvalue3'
    assert output[3]
    assert not output[4]
    assert output[5] == 44


def test_contextsetf_tuple():
    """Simple tuple."""
    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'contextSetf': {
                           'output': ('k1', 'k2', '{ctx3}', True, False, 44)
                       }})

    pypyr.steps.contextsetf.run_step(context)

    output = context['output']
    assert output[0] == 'k1'
    assert output[1] == 'k2'
    assert output[2] == 'ctxvalue3'
    assert output[3]
    assert not output[4]
    assert output[5] == 44


def test_contextsetf_set():
    """Simple set."""
    input_obj = {'k1', 'k2', '{ctx3}', True, False, 44}
    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'contextSetf': {
                           'output': input_obj
                       }})

    pypyr.steps.contextsetf.run_step(context)

    output = context['output']
    assert len(output) == len(input_obj)
    diffs = output - input_obj
    assert len(diffs) == 1
    assert 'ctxvalue3' in diffs


def test_contextsetf_nested():
    """Straight deepish copy with no formatting."""
    # dict containing dict, list, dict-list-dict, tuple, dict-tuple-list
    input_obj = {'k1': 'v1',
                 'k2': 'v2',
                 'k3': 'v3',
                 'k4': [
                     1,
                     2,
                     '3here',
                     {'key4.1': 'value4.1',
                      'key4.2': 'value4.2',
                      'key4.3': {
                          '4.3.1': '4.3.1value',
                          '4.3.2': '4.3.2value'}}
                 ],
                 'k5': {'key5.1': 'value5.1', 'key5.2': 'value5.2'},
                 'k6': ('six6.1', False, [0, 1, 2], 77, 'sixend'),
                 'k7': 'simple string to close 7'
                 }

    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'contextSetf': {
                           'output': input_obj}})

    pypyr.steps.contextsetf.run_step(context)

    output = context['output']
    assert output == input_obj
    assert output is not context
    # verify this was a deep copy - obj refs has to be different for nested
    assert id(output['k4']) != id(input_obj['k4'])
    assert id(output['k4'][3]['key4.3']) != id(input_obj['k4'][3]['key4.3'])
    assert id(output['k5']) != id(input_obj['k5'])
    assert id(output['k6']) != id(input_obj['k6'])
    assert id(output['k6'][2]) != id(input_obj['k6'][2])
    assert id(output['k7']) == id(input_obj['k7'])

    # and proving the theory: mutating output does not touch input
    assert output['k4'][1] == 2
    output['k4'][1] = 88
    assert input_obj['k4'][1] == 2
    assert output['k4'][1] == 88


def test_get_formatted_iterable_nested_with_formatting():
    """Straight deepish copy with formatting."""
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
         'contextSetf': {
             'output': input_obj,
             '{ctx1}': 'substituted key'}})

    pypyr.steps.contextsetf.run_step(context)

    output = context['output']
    assert output != input_obj

    # verify formatted strings
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

    assert context['ctxvalue1'] == 'substituted key'
