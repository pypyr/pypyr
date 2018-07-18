"""default.py unit tests."""
import logging
import pytest
from unittest.mock import patch
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.default


def test_contextdefault_throws_on_empty_context():
    """context must exist."""
    with pytest.raises(KeyNotInContextError):
        pypyr.steps.default.run_step(Context())


def test_contextdefault_throws_on_contextdefault_missing():
    """contextMerge must exist in context."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.default.run_step(Context({'arbkey': 'arbvalue'}))

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['defaults'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.default.\",)")


def test_contextdefault_pass_no_substitutions():
    """contextdefault success case with no substitutions."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'defaults': {
            'key2': 'value4',
            'key4': 'value5'
        }
    })

    pypyr.steps.default.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value2'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'value5'


def test_contextdefault_pass_different_types_with_log():
    """contextdefault success case with substitutions of non strings."""
    context = Context({
        'k1': 33,
        'k2': 123.45,
        'k3': False,
        'defaults': {
            'kint': '{k1}',
            'kfloat': '{k2}',
            'kbool': '{k3}'
        }
    })

    logger = logging.getLogger('pypyr.steps.default')
    with patch.object(logger, 'info') as mock_logger_info:
        pypyr.steps.default.run_step(context)

    mock_logger_info.assert_called_once_with('set 3 context item defaults.')

    assert context['kint'] == '33'
    assert context['k1'] == 33
    assert context['kfloat'] == '123.45'
    assert context['k2'] == 123.45
    assert context['kbool'] == 'False'
    assert not context['k3']


def test_contextdefault_list():
    """Simple list"""
    context = Context({'ctx1': 'ctxvalue1',
                       'ctx2': 'ctxvalue2',
                       'ctx3': 'ctxvalue3',
                       'defaults': {
                           'ctx4': ['k1', 'k2', '{ctx3}', True, False, 44]
                       }})

    pypyr.steps.default.run_step(context)

    assert context['ctx1'] == 'ctxvalue1'
    assert context['ctx2'] == 'ctxvalue2'
    assert context['ctx3'] == 'ctxvalue3'
    assert context['ctx4'] == ['k1', 'k2', 'ctxvalue3', True, False, 44]
