"""py.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.py
import pytest

# region py


def test_py_existing_key():
    """Py expression can update existing key."""
    context = Context({'x': 123, 'py': 'x = abs(-42)'})
    assert context['x'] == 123
    pypyr.steps.py.run_step(context)
    assert context['x'] == 42


def test_py_with_import():
    """Py expression can use imports."""
    context = Context({'y': 4, 'py': 'import math\nx = math.sqrt(y)'})
    assert context['y'] == 4
    assert 'x' not in context
    pypyr.steps.py.run_step(context)
    assert context['x'] == 2
    assert context['y'] == 4


def test_py_single_code():
    """One word python function works."""
    context = Context({'py': 'abs(-1-2)'})
    pypyr.steps.py.run_step(context)


def test_py_sequence():
    """Sequence of py code works and touches context."""
    context = Context({'py': "test = 1;"})
    pypyr.steps.py.run_step(context)

    context.update({'py': "test += 2"})
    pypyr.steps.py.run_step(context)

    context.update({'py': "test += 3"})
    pypyr.steps.py.run_step(context)

    assert context['test'] == 6, "context should be 6 at this point"


def test_py_sequence_with_semicolons():
    """Single py code string with semi - colons works."""
    context = Context({'py':
                       'x = abs(-1); x+= abs(-2); x += abs(-3);'})
    pypyr.steps.py.run_step(context)

    assert context['py'] == 'x = abs(-1); x+= abs(-2); x += abs(-3);'
    assert context['x'] == 6


def test_py_sequence_with_linefeeds():
    """Single py code string with linefeeds works."""
    context = Context({'py':
                       'abs(-1)\nabs(-2)\nabs(-3)'})
    pypyr.steps.py.run_step(context)


def test_py_error_throws():
    """Input pycode error should raise up to caller."""
    with pytest.raises(AssertionError):
        context = Context({'py': 'assert False'})
        pypyr.steps.py.run_step(context)


def test_py_no_context_throw():
    """No pycode in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.py.run_step(context)

    assert str(err_info.value) == ("context['py'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.py.")


def test_py_none_context_throw():
    """None pycode in context should throw assert error."""
    with pytest.raises(KeyInContextHasNoValueError):
        context = Context({'py': None})
        pypyr.steps.py.run_step(context)
# endregion py

# region pycode


def test_pycode_single_code():
    """One word python function works."""
    context = Context({'pycode': 'abs(-1-2)'})
    pypyr.steps.py.run_step(context)


def test_pycode_sequence():
    """Sequence of py code works and touches context."""
    context = Context({'pycode': "context['test'] = 1;"})
    pypyr.steps.py.run_step(context)

    context.update({'pycode': "context['test'] += 2"})
    pypyr.steps.py.run_step(context)

    context.update({'pycode': "context['test'] += 3"})
    pypyr.steps.py.run_step(context)

    assert context['test'] == 6, "context should be 6 at this point"


def test_pycode_sequence_with_semicolons():
    """Single py code string with semi - colons works."""
    context = Context({'pycode':
                       'abs(-1); abs(-2); abs(-3);'})
    pypyr.steps.py.run_step(context)

    assert context == {'pycode':
                       'abs(-1); abs(-2); abs(-3);'}, ("context in and out "
                                                       "the same")


def test_pycode_sequence_with_linefeeds():
    """Single py code string with linefeeds works."""
    context = Context({'pycode':
                       'abs(-1)\nabs(-2)\nabs(-3)'})
    pypyr.steps.py.run_step(context)


def test_pycode_error_throws():
    """Input pycode error should raise up to caller."""
    with pytest.raises(AssertionError):
        context = Context({'pycode': 'assert False'})
        pypyr.steps.py.run_step(context)


def test_pycode_no__context_throw():
    """No pycode in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.py.run_step(context)

    assert str(err_info.value) == ("context['py'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.py.")


def test_pycode_none_context_throw():
    """None pycode in context should throw assert error."""
    with pytest.raises(KeyInContextHasNoValueError):
        context = Context({'pycode': None})
        pypyr.steps.py.run_step(context)

# endregion pycode
