"""pypyr.steps.cmd unit tests."""
from pathlib import Path
import subprocess

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.cmd

cmd_path = Path.cwd().joinpath('tests/testfiles/cmds')
is_windows = config.is_windows


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    return win if is_windows else posix


def test_cmd_str_with_args():
    """Single command string works with string interpolation."""
    cmd = get_cmd('tests/testfiles/cmds/args.sh',
                  r'tests\testfiles\cmds\args.bat')
    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmd': '{d} {a} "{b}" {c}'})
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_str_with_spaces_in_path():
    """Single command string works with spaces in path."""
    cmd = get_cmd('tests/testfiles/cmds/"file with space.sh"',
                  r'tests\testfiles\cmds\file with space.bat')
    context = Context({'a': 'one two',
                       'd': cmd,
                       'cmd': '{d} "{a}"'})
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context

    # and with quotes
    if is_windows:
        context = Context({
            'cmd': r'"tests\testfiles\cmds\file with space.bat" "one two"'})
        pypyr.steps.cmd.run_step(context)

        assert 'cmdOut' not in context


def test_cmd_str_with_args_rel_path_with_backslash():
    """On Windows can use relative path if backslash in path."""
    if is_windows:
        cmd = r'tests\testfiles\cmds\args.bat'
    else:
        cmd = 'tests/testfiles/cmds/args.sh'

    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmd': '{d} {a} "{b}" {c}'})
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_dict_input_with_args():
    """Single command string works with multiple args."""
    cmd = get_cmd('tests/testfiles/cmds/args.sh',
                  r'tests\testfiles\cmds\args.bat')
    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmd': {
                           'run': '{d} {a} "{b}" {c}'}})
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_dict_input_with_string_interpolation_save_out():
    """Single command string works with string interpolation."""
    cmd = get_cmd('echo blah',
                  r'tests\testfiles\cmds\echo.bat blah')
    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': {'run': cmd,
                               'save': True}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 0
    assert context['cmdOut']['stdout'] == 'blah'
    assert not context['cmdOut']['stderr']


def test_cmd_dict_input_sequence_with_cwd():
    """Single command string works with cwd."""
    cmd = get_cmd('pwd', str(cmd_path.joinpath('pwd.bat')))

    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': {'run': cmd,
                               'save': True,
                               'cwd': 'tests'}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 0
    assert Path(context['cmdOut']['stdout']).samefile('./tests')
    assert not context['cmdOut']['stderr']


def test_cmd_dict_input_sequence_with_cwd_interpolate():
    """Single command string works with cwd interpolation."""
    if is_windows:
        # windows path supports front slashes IF it's absolute
        cmd = cmd_path.joinpath('pwd.bat').as_posix()
    else:
        # deliberately testing relative path resolution here
        cmd = 'testfiles/cmds/pwd.sh'

    context = Context({'k1': 'tests',
                       'cmd': {'run': cmd,
                               'save': True,
                               'cwd': '{k1}'}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 0
    assert Path(context['cmdOut']['stdout']).samefile('./tests')
    assert not context['cmdOut']['stderr']


def test_cmd_error_throws():
    """Process returning 1 should throw CalledProcessError with no save."""
    cmd = get_cmd('tests/testfiles/cmds/exit1.sh',
                  r'tests\testfiles\cmds\exit1.bat')
    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': cmd})
        pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_error_throws_with_save_true():
    """Process returning 1 should throw CalledProcessError."""
    cmd = get_cmd('tests/testfiles/cmds/exitwitherr.sh',
                  r'tests\testfiles\cmds\exitwitherr.bat')

    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': {'run': cmd, 'save': True}})
        pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 1
    assert not context['cmdOut']['stdout']
    assert context['cmdOut']['stderr'] == 'arb err here'


def test_cmd_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.cmd.run_step(context)

    assert str(err_info.value) == ("context['cmd'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.cmd.")
