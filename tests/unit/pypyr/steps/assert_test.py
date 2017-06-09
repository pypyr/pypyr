"""assert.py unit tests."""
import importlib
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyNotInContextError,
                          KeyInContextHasNoValueError)
import pytest

assert_step = None


def setup_module(module):
    """Setup any state specific to the execution of the given module."""
    # loading assert dynamically because it clashes with built-in assert
    global assert_step
    assert_step = importlib.import_module('pypyr.steps.assert')


def test_assert_raises_on_empty_context():
    """context must exist."""
    with pytest.raises(AssertionError):
        assert_step.run_step(Context())


def test_assert_raises_on_missing_assertthis():
    """assertThis must exist."""
    context = Context({'k1': 'v1'})
    with pytest.raises(KeyNotInContextError):
        assert_step.run_step(context)


def test_assert_raises_on_empty_assertthis():
    """assertThis must not be empty."""
    context = Context({'assertThis': None})
    with pytest.raises(KeyInContextHasNoValueError):
        assert_step.run_step(context)


def test_assert_raises_on_assertthis_false():
    """assertThis boolean False raises."""
    context = Context({'assertThis': False})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError('assert False evaluated to False.',)")


def test_assert_passes_on_assertthis_true():
    """assertThis boolean True passes."""
    context = Context({'assertThis': True})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_int():
    """assertThis int 1 is True."""
    context = Context({'assertThis': 1})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_arb_int():
    """assertThis non-0 int is True."""
    context = Context({'assertThis': 55})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_arb_negative_int():
    """assertThis non-0 int is True."""
    context = Context({'assertThis': -55})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_float():
    """assertThis non 0 float is True."""
    context = Context({'assertThis': 3.5})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_false_string():
    """assertThis arbitrary string isn't True raises."""
    context = Context({'assertThis': 'arb string'})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError('assert arb string evaluated to False.',)")


def test_assert_raises_on_assertthis_false_int():
    """assertThis int 0 is False."""
    context = Context({'assertThis': 0})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError('assert 0 evaluated to False.',)")


def test_assert_passes_on_assertthis_true_string():
    """assertThis boolean string to True passes."""
    context = Context({'assertThis': 'True'})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals():
    """assertThis does not equal assertEquals."""
    context = Context({'assertThis': 'boom',
                       'assertEquals': 'BOOM'})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type "
        "str and does not equal context['assertEquals'] of type str.\",)")


def test_assert_passes_on_assertthis_equals():
    """assertThis equals assertEquals."""
    context = Context({'assertThis': 'boom',
                       'assertEquals': 'boom'})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_equals_bools():
    """assertThis equals assertEquals true bools."""
    context = Context({'assertThis': True,
                       'assertEquals': True})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_equals_bools_false():
    """assertThis equals assertEquals false bools."""
    context = Context({'assertThis': False,
                       'assertEquals': False})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_bools():
    """assertThis does not equal assertEquals bools."""
    context = Context({'assertThis': True,
                       'assertEquals': False})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type bool and does "
        "not equal context['assertEquals'] of type bool.\",)")


def test_assert_passes_on_assertthis_equals_ints():
    """assertThis equals assertEquals true ints."""
    context = Context({'assertThis': 33,
                       'assertEquals': 33})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_ints():
    """assertThis does not equal assertEquals ints."""
    context = Context({'assertThis': 0,
                       'assertEquals': 23})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type int and does "
        "not equal context['assertEquals'] of type int.\",)")


def test_assert_passes_on_assertthis_equals_floats():
    """assertThis equals assertEquals true ints."""
    context = Context({'assertThis': 123.45,
                       'assertEquals': 123.45})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_floats():
    """assertThis does not equal assertEquals ints."""
    context = Context({'assertThis': 123.45,
                       'assertEquals': 5.432})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type float and "
        "does not equal context['assertEquals'] of type float.\",)")


def test_assert_raises_on_assertthis_not_equals_string_to_int():
    """assertThis does not equal assertEquals string to int conversion."""
    context = Context({'assertThis': '23',
                       'assertEquals': 23})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type str and does "
        "not equal context['assertEquals'] of type int.\",)")


def test_assert_raises_on_assertthis_not_equals_string_to_bool():
    """assertThis string does not equal assertEquals bool."""
    context = Context({'assertThis': True,
                       'assertEquals': 'True'})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type bool and does "
        "not equal context['assertEquals'] of type str.\",)")


def test_assert_passes_on_assertthis_equals_lists():
    """assertThis equals assertEquals true list."""
    context = Context({'assertThis': [1, 2, 3, 4.5],
                       'assertEquals': [1, 2, 3, 4.5]})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_lists():
    """assertThis string does not equal assertEquals list."""
    context = Context({'assertThis': [1, 2, 8, 4.5],
                       'assertEquals': [1, 2, 3, 4.5]})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type list and does "
        "not equal context['assertEquals'] of type list.\",)")


def test_assert_passes_on_assertthis_equals_dicts():
    """assertThis equals assertEquals true dict."""
    context = Context({'assertThis': {'k1': 1, 'k2': [2, 3], 'k3': False},
                       'assertEquals': {'k1': 1, 'k2': [2, 3], 'k3': False}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_dict_to_list():
    """assertThis string does not equal assertEquals dict."""
    context = Context({'assertThis': {'k1': 1, 'k2': [2, 3], 'k3': False},
                       'assertEquals': [1, 2, 3, 4.5]})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type dict and does "
        "not equal context['assertEquals'] of type list.\",)")


def test_assert_raises_on_assertthis_not_equals_dict_to_dict():
    """assertThis string does not equal assertEquals dict."""
    context = Context({'assertThis': {'k1': 1, 'k2': [2, 3], 'k3': False},
                       'assertEquals': {'k1': 1, 'k2': [2, 55], 'k3': False}})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type dict and does "
        "not equal context['assertEquals'] of type dict.\",)")

# ---------------------- substitutions ----------------------------------------


def test_assert_passes_on_assertthis_equals_ints_substitutions():
    """assertThis equals assertEquals true ints with substitutions."""
    context = Context({'k1': 33,
                       'k2': 33,
                       'assertThis': '{k1}',
                       'assertEquals': '{k2}'})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_ints_substitutions():
    """assertThis string does not equal assertEquals bool."""
    context = Context({'k1': 33,
                       'k2': 34,
                       'assertThis': '{k1}',
                       'assertEquals': '{k2}'})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type str and does "
        "not equal context['assertEquals'] of type str.\",)")


def test_assert_passes_on_assertthis_not_equals_bools_substitutions():
    """Format expressions equivocates string True and bool True."""
    context = Context({'k1': True,
                       'k2': 'True',
                       'assertThis': '{k1}',
                       'assertEquals': '{k2}'})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_not_equals_none_substitutions():
    """None equals None."""
    context = Context({'k1': None,
                       'k2': None,
                       'assertThis': '{k1}',
                       'assertEquals': '{k2}'})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_true_substitutions():
    """Format expressions equivocates string True and bool True."""
    context = Context({'k1': True,
                       'k2': 'True',
                       'assertThis': '{k1}'})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_none_substitutions():
    """assertThis string does not equal assertEquals with a None."""
    context = Context({'k1': None,
                       'k2': 34,
                       'assertThis': '{k1}',
                       'assertEquals': '{k2}'})
    with pytest.raises(ContextError):
        assert_step.run_step(context)


def test_assert_raises_on_assertthis_bool_substitutions():
    """assertThis string substituted bool evaluates False."""
    context = Context({'k1': False,
                       'k2': 34,
                       'assertThis': '{k1}'})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError('assert {k1} evaluated to False.',)")


def test_assert_raises_on_assertthis_substitutions_int():
    """Format expressions doesn't equivocates int 1 and bool True."""
    context = Context({'k1': 1,
                       'k2': 'True',
                       'assertThis': '{k1}'})

    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError('assert {k1} evaluated to False.',)")


def test_assert_raises_on_assertthis_none_substitutions():
    """assertThis string substituted None evaluates False."""
    context = Context({'k1': None,
                       'k2': 34,
                       'assertThis': '{k1}'})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError('assert {k1} evaluated to False.',)")


def test_assert_passes_on_assertthis_equals_dicts_substitutions():
    """assertThis equals assertEquals true dict."""
    context = Context({'k1': 'v1',
                       'k2': 'v1',
                       'assertThis': {'k1': 1,
                                      'k2': [2, '{k1}'],
                                      'k3': False},
                       'assertEquals': {'k1': 1,
                                        'k2': [2, '{k2}'],
                                        'k3': False}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_equals_dict_substitutions():
    """assertThis equals assertEquals true dict."""
    context = Context({'k1': 'v1',
                       'k2': 'v1',
                       'dict1': {'k1': 1,
                                 'k2': [2, '{k1}'],
                                 'k3': False},
                       'dict2': {'k1': 1,
                                 'k2': [2, '{k1}'],
                                 'k3': False},
                       'assertThis': '{dict1}',
                       'assertEquals': '{dict2}'})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_dict_to_dict_substitutions():
    """assertThis string does not equal assertEquals dict."""
    context = Context({'k1': 'v1',
                       'k2': 'v2',
                       'assertThis': {'k1': 1,
                                      'k2': [2, '{k1}'],
                                      'k3': False},
                       'assertEquals': {'k1': 1,
                                        'k2': [2, '{k2}'],
                                        'k3': False}})
    with pytest.raises(ContextError) as err_info:
        assert_step.run_step(context)

    assert repr(err_info.value) == (
        "ContextError(\"assert context['assertThis'] is of type dict and does "
        "not equal context['assertEquals'] of type dict.\",)")
