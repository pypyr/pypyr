"""pypyr.steps.shells unit tests.

The bulk of the unit tests are in:
tests/unit/steps/dsl/cmdasync_test.py

For tests involving stdout & stderr set to files, see:
tests/integration/pypyr/steps/cmds_int_test.py
"""
from pathlib import Path

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError, MultiError, SubprocessError
import pypyr.steps.shells

cmd_path = Path.cwd().joinpath('tests/testfiles/cmds')
is_windows = config.is_windows


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    return win if is_windows else posix


def test_shells_str_with_args():
    """Single shell string works with string interpolation."""
    cmd = get_cmd('tests/testfiles/cmds/args.sh',
                  r'tests\testfiles\cmds\args.bat')
    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmds': ['{d} {a} "{b}" {c}']})
    pypyr.steps.shells.run_step(context)

    assert 'cmdOut' not in context


def test_shells_sequence_with_ampersands_save_output():
    """Single shell command string with ampersands works."""
    context = Context({'one': 1,
                       'two': 2,
                       'three': 3,
                       'cmds': {
                           'run': ['echo {one} && echo {two} && echo {three}'],
                           'save': True}
                       })
    pypyr.steps.shells.run_step(context)

    out = context['cmdOut']
    assert len(out) == 1
    out1 = out[0]
    assert out1.returncode == 0
    assert out1.stdout == ('1 \r\n2 \r\n3' if is_windows
                           else '1\n2\n3')
    assert not out1.stderr


def test_shells_dict_input_with_string_interpolation_save_out():
    """Single command string works with string interpolation."""
    context = Context({'cmds': {'run': ["echo blah"],
                                'save': True}})
    pypyr.steps.shells.run_step(context)

    out = context['cmdOut']
    assert len(out) == 1
    out1 = out[0]

    assert out1.returncode == 0
    assert out1.stdout == 'blah'
    assert not out1.stderr


def test_shells_with_cwd():
    """Single command string works with string interpolation."""
    cmd = get_cmd('pwd', 'echo %cd%')
    context = Context({'cmds': {'run': cmd,
                                'save': True,
                                'cwd': 'tests'}})
    pypyr.steps.shells.run_step(context)

    out = context['cmdOut']
    assert len(out) == 1
    out1 = out[0]

    assert out1.returncode == 0
    assert Path(out1.stdout).samefile('tests')
    assert not out1.stderr


def test_shells_error_throws():
    """Shell process returning 1 should throw CalledProcessError."""
    with pytest.raises(MultiError) as the_err:
        context = Context({'cmds': 'exit 1'})
        pypyr.steps.shells.run_step(context)

    err = the_err.value
    assert len(err) == 1
    assert isinstance(err[0], SubprocessError)


def test_shells_empty_context_cmd_throw():
    """Empty cmds in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.shells.run_step(context)

    assert str(err_info.value) == ("context['cmds'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.shells.")
