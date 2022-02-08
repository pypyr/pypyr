"""safeshell.py unit tests."""
from pathlib import Path

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.safeshell

cmd_path = Path.cwd().joinpath('tests/testfiles/cmds')
is_windows = config.is_windows


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    if is_windows:
        return str(cmd_path.joinpath(win))
    return posix


def test_safeshell_str_with_args():
    """Single command string works with string interpolation."""
    cmd = get_cmd('tests/testfiles/cmds/args.sh',
                  'args.bat')
    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmd': '{d} {a} "{b}" {c}'})
    pypyr.steps.safeshell.run_step(context)

    assert 'cmdOut' not in context


def test_safeshell_dict_input_with_args():
    """Single command string works with multiple args."""
    cmd = get_cmd('tests/testfiles/cmds/args.sh',
                  'args.bat')
    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmd': {
                           'run': '{d} {a} "{b}" {c}'}})
    pypyr.steps.safeshell.run_step(context)

    assert 'cmdOut' not in context


def test_empty_context_safeshell_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.safeshell.run_step(context)

    assert str(err_info.value) == ("context['cmd'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.cmd.")
