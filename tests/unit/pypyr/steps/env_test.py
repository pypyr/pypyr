"""env.py unit tests."""
import os
import pytest
from unittest.mock import patch, DEFAULT
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.env

# ------------------------- env base -----------------------------------------#


def test_env_throws_on_empty_context():
    """Context must exist."""
    with pytest.raises(AssertionError) as err_info:
        pypyr.steps.env.run_step(None)

    assert str(err_info.value) == ("context must have value "
                                   "for pypyr.steps.env")


def test_env_throws_if_all_env_context_missing():
    """Env context keys must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.env.run_step(Context({'arbkey': 'arbvalue'}))

    assert str(err_info.value) == ("context['env'] doesn't exist. It must "
                                   "exist for pypyr.steps.env.")


def test_env_throws_if_env_context_wrong_type():
    """Env context keys must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.env.run_step(
            Context({'env': {'envSet': 'it shouldnt be a string'}}))

    assert str(err_info.value) == ("context must contain "
                                   "any combination of env['get'], env['set'] "
                                   "or env['unset'] for pypyr.steps.env")


def test_env_only_calls_get():
    """Call only get."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'get': {
            'key2': 'ARB_GET_ME1',
            'key4': 'ARB_GET_ME2'
        }}
    })

    with patch.multiple('pypyr.steps.env',
                        env_get=DEFAULT,
                        env_set=DEFAULT,
                        env_unset=DEFAULT
                        ) as mock_env:
        pypyr.steps.env.run_step(context)

    mock_env['env_get'].assert_called_once()
    mock_env['env_set'].assert_called_once()
    mock_env['env_unset'].assert_called_once()


def test_env_only_calls_set():
    """Call only set."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'set': {
            'ARB_SET_ME1': 'key2',
            'ARB_SET_ME2': 'key1'
        }}
    })

    with patch.multiple('pypyr.steps.env',
                        env_get=DEFAULT,
                        env_set=DEFAULT,
                        env_unset=DEFAULT
                        ) as mock_env:
        pypyr.steps.env.run_step(context)

    mock_env['env_get'].assert_called_once()
    mock_env['env_set'].assert_called_once()
    mock_env['env_unset'].assert_called_once()


def test_env_only_calls_unset():
    """Call only unset."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'unset': [
            'ARB_DELETE_ME1',
            'ARB_DELETE_ME2'
        ]}
    })

    with patch.multiple('pypyr.steps.env',
                        env_get=DEFAULT,
                        env_set=DEFAULT,
                        env_unset=DEFAULT
                        ) as mock_env:
        pypyr.steps.env.run_step(context)

    mock_env['env_get'].assert_called_once()
    mock_env['env_set'].assert_called_once()
    mock_env['env_unset'].assert_called_once()


def test_env_all_operations():
    """Env should run all specified operations."""
    os.environ['ARB_GET_ME1'] = 'arb value from $ENV ARB_GET_ME1'
    os.environ['ARB_GET_ME2'] = 'arb value from $ENV ARB_GET_ME2'
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb value from $ENV ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {
                'get': {
                    'key2': 'ARB_GET_ME1',
                    'key4': 'ARB_GET_ME2'},
                'set': {
                    'ARB_SET_ME1': 'value 4',
                    'ARB_SET_ME2': 'go go {key2} end end'},
                'unset': [
                    'ARB_DELETE_ME1',
                    'ARB_DELETE_ME2']}
    })

    pypyr.steps.env.run_step(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'arb value from $ENV ARB_GET_ME1'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'arb value from $ENV ARB_GET_ME2'
    assert os.environ['ARB_SET_ME1'] == 'value 4'
    assert os.environ['ARB_SET_ME2'] == ('go go arb value from '
                                         '$ENV ARB_GET_ME1 end end')
    assert 'ARB_DELETE_ME1' not in os.environ
    assert 'ARB_DELETE_ME2' not in os.environ

    del os.environ['ARB_GET_ME1']
    del os.environ['ARB_GET_ME2']
    del os.environ['ARB_SET_ME1']
    del os.environ['ARB_SET_ME2']

# ------------------------- env base -----------------------------------------#
#
# ------------------------- envGet -------------------------------------------#


def test_envget_pass():
    """Env get success case."""
    os.environ['ARB_DELETE_ME1'] = 'arb value from $ENV ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb value {from} $ENV ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'keyname': 'key',
        'delete_substitute': 'DELETE',
        'env': {'get': {
            'key2': 'ARB_DELETE_ME1',
            '{keyname}4': 'ARB_{delete_substitute}_ME2'
        }}
    })

    pypyr.steps.env.env_get(context)

    assert context['key1'] == 'value1'
    assert context['key2'] == 'arb value from $ENV ARB_DELETE_ME1'
    assert context['key3'] == 'value3'
    assert context['key4'] == 'arb value {from} $ENV ARB_DELETE_ME2'

    del os.environ['ARB_DELETE_ME1']
    del os.environ['ARB_DELETE_ME2']


def test_envget_env_doesnt_exist():
    """Env get when $ENV doesn't exist."""
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'
    try:
        del os.environ['ARB_DELETE_ME1']
    except KeyError:
        pass

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'get': {
            'key2': 'ARB_DELETE_ME1',
            'key4': 'ARB_DELETE_ME2'
        }}
    })

    with pytest.raises(KeyError) as err_info:
        pypyr.steps.env.env_get(context)

    assert str(err_info.value) == "'ARB_DELETE_ME1'"
    del os.environ['ARB_DELETE_ME2']


def test_envget_returns_false():
    """Env get returns false if env>get not specified."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'Xget': {
            'key2': 'ARB_DELETE_ME1'
        }}
    })

    assert not pypyr.steps.env.env_get(context)
# ------------------------- envGet -------------------------------------------#

# ------------------------- envSet -------------------------------------------#


def test_envset_pass():
    """Env set success case."""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'set': {
            'ARB_DELETE_ME1': 'text value 2',
            'ARB_DELETE_ME2': 'text value 1'
        }}
    })

    assert pypyr.steps.env.env_set(context)

    assert os.environ['ARB_DELETE_ME1'] == 'text value 2'
    assert os.environ['ARB_DELETE_ME2'] == 'text value 1'

    del os.environ['ARB_DELETE_ME1']
    del os.environ['ARB_DELETE_ME2']


def test_envset_with_string_interpolation():
    """Env set success case."""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'del_substitute': 'DELETE',
        'env': {'set': {
            'ARB_DELETE_ME1': 'blah blah {key2} and {key1} goes here.',
            'ARB_DELETE_ME2': 'plain old string',
            'ARB_{del_substitute}_ME3': '{key3}'
        }}
    })

    assert pypyr.steps.env.env_set(context)

    assert os.environ['ARB_DELETE_ME1'] == ('blah blah value2 and value1 goes '
                                            'here.')
    assert os.environ['ARB_DELETE_ME2'] == 'plain old string'
    assert os.environ['ARB_DELETE_ME3'] == 'value3'

    del os.environ['ARB_DELETE_ME1']
    del os.environ['ARB_DELETE_ME2']
    del os.environ['ARB_DELETE_ME3']


def test_envset_returns_false():
    """Env set returns false if env>set doesn't exist.."""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'blah': {
            'ARB_DELETE_ME1': 'blah blah {key2} and {key1} goes here.'
        }}
    })

    assert not pypyr.steps.env.env_set(context)

# ------------------------- envSet -------------------------------------------#

# ------------------------- envUnset -----------------------------------------#


def test_envunset_pass():
    """Env unset success case."""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    os.environ['ARB_DELETE_ME1'] = 'arb from pypyr context ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'unset': [
            'ARB_DELETE_ME1',
            'ARB_DELETE_ME2'
        ]}
    })

    assert pypyr.steps.env.env_unset(context)

    assert 'ARB_DELETE_ME1' not in os.environ
    assert 'ARB_DELETE_ME2' not in os.environ


def test_envunset_pass_wuth_interpolation():
    """Env unset success case with interpolation."""
    # Deliberately have 1 pre-existing $ENV to update, and 1 unset so can
    # create it anew as part of test
    os.environ['ARB_DELETE_ME1'] = 'arb from pypyr context ARB_DELETE_ME1'
    os.environ['ARB_DELETE_ME2'] = 'arb from pypyr context ARB_DELETE_ME2'

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        "one": 1,
        'del': 'DELETE',
        'del_full': 'ARB_DELETE_ME2',
        'env': {'unset': [
            'ARB_{del}_ME{one}',
            '{del_full}'
        ]}
    })

    assert pypyr.steps.env.env_unset(context)

    assert 'ARB_DELETE_ME1' not in os.environ
    assert 'ARB_DELETE_ME2' not in os.environ


def test_envunset_doesnt_exist():
    """Env unset success case where env doesn't exist."""
    # Make sure $ENV isn't set
    try:
        del os.environ['ARB_DELETE_SNARK']
    except KeyError:
        pass

    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'env': {'unset': [
                'ARB_DELETE_SNARK'
                ]}
    })

    assert pypyr.steps.env.env_unset(context)

    assert 'ARB_DELETE_SNARK' not in os.environ


def test_envunset_returns_false():
    """Env unset returns false if not env>unset not specified.."""
    context = Context({
        'env': {'set': {
            'ARB_DELETE_ME1': 'blah blah {key2} and {key1} goes here.'
        }}
    })

    assert not pypyr.steps.env.env_unset(context)
# ------------------------- envUnset -----------------------------------------#
