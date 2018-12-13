"""expressions.py unit tests."""

from math import sqrt
import pytest
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.utils.expressions as expressions


def test_simple_expr_none_dict():
    """Simple expression passes, with no locals dict."""
    assert expressions.eval_string('1+1', None) == 2


def test_simple_expr_empty_dict():
    """Simple expression passes, with no locals dict."""
    out = expressions.eval_string('len("123456") < 5', {})
    assert isinstance(out, bool)
    assert not out


def test_simple_expr_locals_dict():
    """Simple expression passes, with locals dict."""
    assert expressions.eval_string('sqrt(4)', {'sqrt': sqrt}) == 2


def test_expr_dict_vars():
    """Expression uses vars from input dict."""
    assert expressions.eval_string('(k1 + k2)*2==10', {'k1': 2, 'k2': 3})


def test_expr_dict_nested_vars():
    """Expression uses nested vars from input dict."""
    assert expressions.eval_string('k2[2]["k2.2"] == 1.23',
                                   {'k1': 1,
                                    'k2': [0,
                                           1,
                                           {'k2.2': 1.23}
                                           ]
                                    }
                                   )


def test_expr_evals_bool():
    """Expression can work as a boolean type."""
    out = expressions.eval_string("a", {'a': True})
    assert isinstance(out, bool)
    assert out


def test_expr_evals_complex():
    """Expression evaluates complex types."""
    assert expressions.eval_string('{"a": "b"} == c', {'c': {'a': 'b'}})


def test_expr_runtime_error():
    """Expression raises expected type during runtime error."""
    with pytest.raises(ZeroDivisionError):
        expressions.eval_string('1/0', None)


def test_expr_invalid_syntax():
    """Expression raises when invalid sytntax on input."""
    with pytest.raises(SyntaxError):
        expressions.eval_string('invalid code here', None)


def test_expr_var_doesnt_exist():
    """Expression raises when variable not found in namespace."""
    with pytest.raises(NameError):
        expressions.eval_string('a', {'b': True})


def test_expr_derived_dicts_fail():
    """Derived dicts fail with eval.

    For reasons best known to eval(), it EAFPs the locals() look-up 1st and if
    it raises a KeyNotFound error, moves on to globals.

    This means if you pass in something like the pypyr context, the custom
    KeyNotInContextError the pypyr context raises isn't caught, and thus eval
    doesn't work.

    Therefore, before pypyr context needs to initialize a new dict(context) in
    order to be used as the locals arg.

    If this unit test fails, it means the functionality has changed and you can
    get rid of the redundant dict creation when context get_eval_string invokes
    expressions eval_string.
    """
    with pytest.raises(KeyNotInContextError):
        assert expressions.eval_string(
            'len([0,1,2])', Context({'k1': 'v1'})) == 3
