"""pypyr.steps.envget unit tests."""
import logging
import os
import pytest
from pypyr.context import Context
from pypyr.errors import ContextError, KeyNotInContextError
import pypyr.steps.envget

# ------------------------- run_step -----------------------------------------#
from tests.common.utils import patch_logger


def test_envget_throws_on_empty_context():
    """Context must exist."""
    with pytest.raises(AssertionError) as err_info:
        pypyr.steps.envget.run_step(None)

    assert str(err_info.value) == ("context must have value "
                                   "for pypyr.steps.envget")


def test_envget_throws_if_envget_context_missing():
    """Env context keys must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.envget.run_step(Context({'arbkey': 'arbvalue'}))

    assert str(err_info.value) == ("context['envGet'] doesn't exist. It must "
                                   "exist for pypyr.steps.envget.")


def test_envget_throws_if_env_context_wrong_type():
    """Env context keys must exist."""
    with pytest.raises(ContextError) as err_info:
        pypyr.steps.envget.run_step(
            Context({'envGet': 'it shouldnt be a string'}))

    assert str(err_info.value) == ("envGet must contain a list of dicts.")


def test_envget_pass():
    """Env get success case."""
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb value from $ENV ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envGet': [
            {'env': 'ARB_DELETE_ME1',
             'key': 'key2',
             'default': 'blah'},
            {'env': 'ARB_DELETE_ME2',
             'key': 'key3'},
            {'env': 'ARB_XXX_IDONTEXIST_BLAH',
             'key': 'key4',
             'default': 'blah4'},
            {'env': 'ARB_XXX_IDONTEXIST_BLAH',
             'key': 'key5'}
        ]
    })

    with patch_logger('pypyr.steps.envget', logging.INFO) as mock_logger_info:
        pypyr.steps.envget.run_step(context)

    del os.environ['ARB_DELETE_ME1']
    del os.environ['ARB_DELETE_ME2']

    mock_logger_info.assert_called_once_with('saved 3 $ENVs to context.')

    assert context['key1'] == 'value1'
    assert context['key2'] == 'arb value from $ENV ARB_DELETE_ME1'
    assert context['key3'] == 'arb value from $ENV ARB_DELETE_ME2'
    assert context['key4'] == 'blah4'
    assert 'key5' not in context


def test_envget_pass_single_item():
    """Env get success case where single item not list passed."""
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envGet':
            {'env': 'ARB_DELETE_ME1',
             'key': 'key2',
             'default': 'blah'}
    })

    pypyr.steps.envget.run_step(context)

    del os.environ['ARB_DELETE_ME1']

    assert context['key1'] == 'value1'
    assert context['key2'] == 'arb value from $ENV ARB_DELETE_ME1'
    assert context['key3'] == 'value3'
    assert 'key5' not in context


def test_envget_pass_nones():
    """Env get success case with none/nulls."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'envGet': [
            {'env': 'ARB_XXX_IDONTEXIST_BLAH',
             'key': 'key4',
             'default': None}
        ]
    })

    pypyr.steps.envget.run_step(context)

    assert context['key4'] is None


def test_envget_pass_with_substitutions():
    """Env get success case with string substitutions."""
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'env_val1': 'ARB_DELETE_ME1',
        'env_val2': 'ARB_DELETE_ME2',
        'default_val': 'blah',
        'key_val': 'key3',
        'envGet': [
            {'env': '{env_val1}',
             'key': '{key_val}',
             'default': 'blah'},
            {'env': '{env_val2}',
             'key': 'key4',
             'default': '{default_val}'}
        ]
    })

    pypyr.steps.envget.run_step(context)

    del os.environ['ARB_DELETE_ME1']

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value2'
    assert context['key3'] == 'arb value from $ENV ARB_DELETE_ME1'
    assert context['key4'] == 'blah'


def test_envget_pass_with_substitutions_default_not_string():
    """Env get success case with substitutions that aren't string."""
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'env_val1': 'ARB_DELETE_ME1',
        'env_val2': 'ARB_DELETE_ME2',
        'default_val': [0, 1, 2],
        'key_val': 'key3',
        'key_key': 'key',
        'envGet': [
            {'env': '{env_val1}',
             '{key_key}': '{key_val}',
             'default': 'blah'},
            {'env': '{env_val2}',
             'key': 'key4',
             'default': '{default_val}'}
        ]
    })

    pypyr.steps.envget.run_step(context)

    del os.environ['ARB_DELETE_ME1']

    assert context['key1'] == 'value1'
    assert context['key2'] == 'value2'
    assert context['key3'] == 'arb value from $ENV ARB_DELETE_ME1'
    assert context['key4'] == [0, 1, 2]

# ------------------------- get_args -----------------------------------------#


def test_get_args_not_a_dict():
    """Env context keys must exist."""
    with pytest.raises(ContextError) as err_info:
        pypyr.steps.envget.get_args('it shouldnt be a string')

    assert str(err_info.value) == ("envGet must contain a list of dicts.")


def test_get_args_env_exists():
    """Env must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.envget.get_args({'blah': 'blah'})

    assert str(err_info.value) == (
        "context envGet[env] must exist in context for envGet.")


def test_get_args_empty_env_raises():
    """Env must not be empty."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.envget.get_args({'env': None})

    assert str(err_info.value) == (
        "context envGet[env] must exist in context for envGet.")


def test_get_args_key_exists():
    """Key must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.envget.get_args({'env': 'v'})

    assert str(err_info.value) == (
        "context envGet[key] must exist in context for envGet.")


def test_get_args_empty_key_raises():
    """Empty key must raise."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.envget.get_args({'env': 'v', 'key': ''})

    assert str(err_info.value) == (
        "context envGet[key] must exist in context for envGet.")


def test_get_args_no_default():
    """Parses with no default set."""
    (env, key, has_default, default) = pypyr.steps.envget.get_args(
        {'env': 'e', 'key': 'k'})

    assert env == 'e'
    assert key == 'k'
    assert not has_default
    assert default is None


def test_get_args_with_default():
    """Parses with default set."""
    (env, key, has_default, default) = pypyr.steps.envget.get_args(
        {'env': 'e', 'key': 'k', 'default': 'blah'})

    assert env == 'e'
    assert key == 'k'
    assert has_default
    assert default == 'blah'


def test_get_args_with_none_default():
    """Parses with none default set."""
    (env, key, has_default, default) = pypyr.steps.envget.get_args(
        {'env': 'e', 'key': 'k', 'default': None})

    assert env == 'e'
    assert key == 'k'
    assert has_default
    assert default is None
# ------------------------- END get_args -------------------------------------#
