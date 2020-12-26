"""pyimport.py unit tests."""
import builtins
from pathlib import Path

from pypyr.context import Context
from pypyr.dsl import PyString
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.pyimport as pyimport
import pytest


def test_pyimport_none():
    """No pyimport input raises."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pyimport.run_step(context)

    assert str(err_info.value) == ("context['pyImport'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.pyimport.")


def test_pyimport_key_exists_but_none():
    """None source string raises."""
    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        context = Context({'pyImport': None})
        pyimport.run_step(context)

    assert str(err_info.value) == (
        "context['pyImport'] must have a value for pypyr.steps.pyimport.")


def test_pyimport_empty():
    """Empty source string imports nothing."""
    context = Context({'pyImport': ''})
    pyimport.run_step(context)
    assert context._pystring_globals == {}
    # only builtins
    assert list(dict.items(context._pystring_namespace)) == [
        ('__builtins__', builtins.__dict__)]


def test_pyimport():
    """Import namespace saved to context."""
    source = """\
import math

import tests.arbpack.arbmod
import tests.arbpack.arbmod2

from tests.arbpack.arbmultiattr import arb_attr, arb_func as y
"""
    context = Context({'pyImport': source})
    pyimport.run_step(context)
    ns = context._pystring_globals
    len(ns) == 4

    assert ns['math'].sqrt(4) == 2
    # no return value but shouldn't raise not found.
    ns['tests'].arbpack.arbmod.arbmod_attribute()
    assert ns['arb_attr'] == 123.456
    assert ns['y']('ab3') == 'ab3'

    # parent did not import anything NOT specified.
    # tests.arbpack.arbstep exists but wasn't specified for import.
    assert not hasattr(ns['tests'].arbpack, 'arbstep')
    # python has a quirk where if a submodule was imported anywhere else, it's
    # imported & cached for the global namespace of the parent package. So
    # arbmod3, which is used elsewhere in unit tests, might well be an
    # attribute of arbpack here even though not explicitly specified, if part
    # of the test-run included any code somewhere doing
    # import tests.arbpack.arbmod3.
    #
    # importlib.invalidate_caches() doesn't help
    # assert not hasattr(ns['tests'].arbpack, 'arbmod3') --> will FAIL


def test_pyimport_update_not_replace():
    """Import updates/merges to namespace dict, not overwrite."""
    context = Context({'pyImport': 'import math; import tests.arbpack.arbmod'})
    pyimport.run_step(context)

    context['pyImport'] = """\
from pathlib import Path
import tests.arbpack.arbmod3
"""

    # 2nd run should merge into ns dict, not overwrite.
    pyimport.run_step(context)
    ns = context._pystring_globals
    len(ns) == 3

    assert ns['math'].sqrt(4) == 2
    # both the arbpack imports valid because of python submodule global imports
    ns['tests'].arbpack.arbmod.arbmod_attribute()
    assert ns['tests'].arbpack.arbmod3.arb_func_in_arbmod3('ab3') == 'ab3'
    assert ns['Path'].cwd() == Path.cwd()


def test_pyimport_with_pystring():
    """Pystring evals with the globals namespace from pyimport."""
    context = Context({'a': -1,
                       'b': 'xx',
                       'c': 4,
                       'pyImport': 'import math',
                       'out': PyString('abs(a) + len(b) + math.sqrt(c)')})
    pyimport.run_step(context)

    assert context.get_formatted('out') == 5
