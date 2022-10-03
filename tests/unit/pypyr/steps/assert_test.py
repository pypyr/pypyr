"""assert.py unit tests."""
import importlib
import pytest
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError


# loading assert dynamically because it clashes with built-in assert
assert_step = importlib.import_module('pypyr.steps.assert')


def test_assert_raises_on_empty_context():
    """Context must exist."""
    with pytest.raises(AssertionError):
        assert_step.run_step(Context())


def test_assert_raises_on_missing_assert():
    """Assert this must exist."""
    context = Context({'k1': 'v1'})
    with pytest.raises(KeyNotInContextError):
        assert_step.run_step(context)


def test_assert_raises_on_empty_assert():
    """Assert can't be empty."""
    context = Context({'assert': None})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert None evaluated to False."


def test_assert_raises_on_empty_assertthis():
    """Assert this must not be empty."""
    context = Context({'assert': {'this': None}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert None evaluated to False."


def test_assert_passes_on_bare_assert_true():
    """Assert bare boolean True passes."""
    context = Context({'assert': True})
    assert_step.run_step(context)


def test_assert_raises_on_bare_assert_false():
    """Assert bare boolean False raises."""
    context = Context({'assert': False})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert False evaluated to False."


def test_assert_raises_on_assertthis_false():
    """Assert this boolean False raises."""
    context = Context({'assert': {'this': False}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert False evaluated to False."


def test_assert_passes_on_assertthis_true():
    """Assert this boolean True passes."""
    context = Context({'assert': {'this': True}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_int():
    """Assert this int 1 is True."""
    context = Context({'assert': {'this': 1}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_arb_int():
    """Assert this non-0 int is True."""
    context = Context({'assert': {'this': 55}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_arb_negative_int():
    """Assert this non-0 int is True."""
    context = Context({'assert': {'this': -55}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_float():
    """Assert this non 0 float is True."""
    context = Context({'assert': {'this': 3.5}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_false_string():
    """Assert this arbitrary string isn't True raises."""
    context = Context({'assert': {'this': 'arb string'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert arb string evaluated to False."


def test_assert_raises_on_assertthis_false_int():
    """Assert this int 0 is False."""
    context = Context({'assert': {'this': 0}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert 0 evaluated to False."


def test_assert_passes_on_assertthis_true_string():
    """Assert this boolean string to True passes."""
    context = Context({'assert': {'this': 'True'}})
    assert_step.run_step(context)


def test_assert_arb_dict():
    """Arbitrary dict evaluates as truthy."""
    context = Context({'assert': {
        'arb': 'BOOM'}})

    assert_step.run_step(context)


def test_assert_arb_empty_dict():
    """Arbitrary empty dict evaluates as truthy."""
    context = Context({'assert': {}})

    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert {} evaluated to False."


def test_assert_raises_on_assertequals_without_this():
    """Assert raises if equals without this."""
    context = Context({'assert': {
        'equals': 'BOOM'}})
    with pytest.raises(KeyNotInContextError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "you have to set assert.this to use assert.equals.")


def test_assert_raises_on_assertthis_not_equals():
    """Assert this does not equal assertEquals."""
    context = Context({'assert': {
        'this': 'boom',
        'equals': 'BOOM'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type "
        "str and does not equal assert['equals'] of type str.")


def test_assert_passes_on_assertthis_equals():
    """Assert this equals assertEquals."""
    context = Context({'assert': {'this': 'boom',
                                  'equals': 'boom'}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_equals_bools():
    """Assert this equals assertEquals true bools."""
    context = Context({'assert': {'this': True,
                                  'equals': True}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_equals_bools_false():
    """Assert this equals assertEquals false bools."""
    context = Context({'assert':
                       {'this': False,
                        'equals': False}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_bools():
    """Assert this does not equal assertEquals bools."""
    context = Context({'assert': {'this': True,
                                  'equals': False}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type bool and does "
        "not equal assert['equals'] of type bool.")


def test_assert_passes_on_assertthis_equals_ints():
    """Assert this equals assertEquals true ints."""
    context = Context({'assert': {'this': 33,
                                  'equals': 33}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_ints():
    """Assert this does not equal assertEquals ints."""
    context = Context({'assert': {'this': 0,
                                  'equals': 23}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type int and does "
        "not equal assert['equals'] of type int.")


def test_assert_passes_on_assertthis_equals_floats():
    """Assert this equals assertEquals true ints."""
    context = Context({'assert': {'this': 123.45,
                                  'equals': 123.45}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_floats():
    """Assert this does not equal assertEquals ints."""
    context = Context({'assert': {'this': 123.45,
                                  'equals': 5.432}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type float and "
        "does not equal assert['equals'] of type float.")


def test_assert_raises_on_assertthis_not_equals_string_to_int():
    """Assert this does not equal assertEquals string to int conversion."""
    context = Context({'assert': {'this': '23',
                                  'equals': 23}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type str and does "
        "not equal assert['equals'] of type int.")


def test_assert_raises_on_assertthis_not_equals_string_to_bool():
    """Assert this string does not equal assertEquals bool."""
    context = Context({'assert': {'this': True,
                                  'equals': 'True'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type bool and does "
        "not equal assert['equals'] of type str.")


def test_assert_passes_on_assertthis_equals_lists():
    """Assert this equals assertEquals true list."""
    context = Context({'assert': {'this': [1, 2, 3, 4.5],
                                  'equals': [1, 2, 3, 4.5]}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_lists():
    """Assert this string does not equal assertEquals list."""
    context = Context({'assert': {'this': [1, 2, 8, 4.5],
                                  'equals': [1, 2, 3, 4.5]}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type list and does "
        "not equal assert['equals'] of type list.")


def test_assert_passes_on_assertthis_equals_dicts():
    """Assert this equals assertEquals true dict."""
    context = Context({'assert': {
        'this': {'k1': 1, 'k2': [2, 3], 'k3': False},
        'equals': {'k1': 1, 'k2': [2, 3], 'k3': False}}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_dict_to_list():
    """Assert this string does not equal assertEquals dict."""
    context = Context({'assert': {'this': {'k1': 1, 'k2': [2, 3], 'k3': False},
                                  'equals': [1, 2, 3, 4.5]}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type dict and does "
        "not equal assert['equals'] of type list.")


def test_assert_raises_on_assertthis_not_equals_dict_to_dict():
    """Assert this string does not equal assertEquals dict."""
    context = Context({'assert': {
        'this': {'k1': 1, 'k2': [2, 3], 'k3': False},
        'equals': {'k1': 1, 'k2': [2, 55], 'k3': False}}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type dict and does "
        "not equal assert['equals'] of type dict.")


def test_assert_raises_on_assertthis_with_msg():
    """Assert this uses custom error message."""
    context = Context({'assert': {'this': False,
                                  'msg': "arb"}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "arb"

# region substitutions


def test_assert_raises_on_assertthis_with_msg_substitutions():
    """Assert this uses custom error message."""
    context = Context({'k1': 'arb',
                       'assert': {'this': False,
                                  'msg': 'x{k1}x'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "xarbx"


def test_assert_passes_on_bare_assert_substitutions():
    """Assert bare boolean substitutes to int passes."""
    context = Context({'k1': 33, 'assert': '{k1}'})
    assert_step.run_step(context)


def test_assert_raises_on_bare_assert_substitutions():
    """Assert bare with substitution raises."""
    context = Context({'k1': 0, 'assert': '{k1}'})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert {k1} evaluated to False."


def test_assert_passes_on_assertthis_equals_ints_substitutions():
    """Assert this equals assertEquals true ints with substitutions."""
    context = Context({'k1': 33,
                       'k2': 33,
                       'assert': {'this': '{k1}',
                                  'equals': '{k2}'}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_ints_substitutions():
    """Assert this string does not equal assertEquals int."""
    context = Context({'k1': 33,
                       'k2': 34,
                       'assert': {'this': '{k1}',
                                  'equals': '{k2}'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type int and does "
        "not equal assert['equals'] of type int.")


def test_assert_passes_on_assertthis_not_equals_bools_substitutions():
    """Format expressions doesn't equivocate string True and bool True."""
    context = Context({'k1': True,
                       'k2': 'True',
                       'assert': {'this': '{k1}',
                                  'equals': '{k2}'}})

    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type bool and does "
        "not equal assert['equals'] of type str.")


def test_assert_passes_on_assertthis_not_equals_none_substitutions():
    """None equals None."""
    context = Context({'k1': None,
                       'k2': None,
                       'assert': {'this': '{k1}',
                                  'equals': '{k2}'}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_true_substitutions():
    """Format expressions equivocates string True and bool True."""
    context = Context({'k1': True,
                       'k2': 'True',
                       'assert': {'this': '{k1}'}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_none_substitutions():
    """Assert this string does not equal assertEquals with a None."""
    context = Context({'k1': None,
                       'k2': 34,
                       'assert': {'this': '{k1}',
                                  'equals': '{k2}'}})
    with pytest.raises(AssertionError):
        assert_step.run_step(context)


def test_assert_raises_on_assertthis_bool_substitutions():
    """Assert this string substituted bool evaluates False."""
    context = Context({'k1': False,
                       'k2': 34,
                       'assert': {'this': '{k1}'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert {k1} evaluated to False."


def test_assert_raises_on_assertthis_substitutions_int():
    """Format expressions doesn't equivocates int 0 and bool True."""
    context = Context({'k1': 0,
                       'k2': 'True',
                       'assert': {'this': '{k1}'}})

    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert {k1} evaluated to False."


def test_assert_assertthis_int_1_is_true():
    """Format expressions equivocates int 1 and bool True."""
    context = Context({'k1': 1,
                       'k2': 'True',
                       'assert': {'this': '{k1}'}})

    assert_step.run_step(context)


def test_assert_raises_on_assertthis_none_substitutions():
    """Assert this string substituted None evaluates False."""
    context = Context({'k1': None,
                       'k2': 34,
                       'assert': {'this': '{k1}'}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == "assert {k1} evaluated to False."


def test_assert_passes_on_assertthis_equals_dicts_substitutions():
    """Assert this equals assertEquals true dict."""
    context = Context({'k1': 'v1',
                       'k2': 'v1',
                       'assert': {'this': {'k1': 1,
                                           'k2': [2, '{k1}'],
                                           'k3': False},
                                  'equals': {'k1': 1,
                                             'k2': [2, '{k2}'],
                                             'k3': False}}})
    assert_step.run_step(context)


def test_assert_passes_on_assertthis_equals_dict_substitutions():
    """Assert this equals assertEquals true dict."""
    context = Context({'k1': 'v1',
                       'k2': 'v1',
                       'dict1': {'k1': 1,
                                 'k2': [2, '{k1}'],
                                 'k3': False},
                       'dict2': {'k1': 1,
                                 'k2': [2, '{k1}'],
                                 'k3': False},
                       'assert': {'this': '{dict1}',
                                  'equals': '{dict2}'}})
    assert_step.run_step(context)


def test_assert_raises_on_assertthis_not_equals_dict_to_dict_substitutions():
    """Assert this string does not equal assertEquals dict."""
    context = Context({'k1': 'v1',
                       'k2': 'v2',
                       'assert': {'this': {'k1': 1,
                                           'k2': [2, '{k1}'],
                                           'k3': False},
                                  'equals': {'k1': 1,
                                             'k2': [2, '{k2}'],
                                             'k3': False}}})
    with pytest.raises(AssertionError) as err_info:
        assert_step.run_step(context)

    assert str(err_info.value) == (
        "assert assert['this'] is of type dict and does "
        "not equal assert['equals'] of type dict.")

# endregion substitutions
