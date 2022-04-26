"""pypyr.steps.shell unit tests."""
from pathlib import Path
import subprocess

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.shell

cmd_path = Path.cwd().joinpath('tests/testfiles/cmds')
is_windows = config.is_windows


def get_cmd(posix, win):
    """Return posix or win depending on current platform."""
    return win if is_windows else posix


def test_shell_str_with_args():
    """Single shell string works with string interpolation."""
    cmd = get_cmd('tests/testfiles/cmds/args.sh',
                  r'tests\testfiles\cmds\args.bat')
    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd,
                       'cmd': '{d} {a} "{b}" {c}'})
    pypyr.steps.shell.run_step(context)

    assert 'cmdOut' not in context


def test_shell_sequence_with_ampersands():
    """Single shell command string with ampersands works."""
    context = Context({'one': 1,
                       'two': 2,
                       'three': 3,
                       'cmd':
                       'echo {one} && echo {two} && echo {three}'})
    pypyr.steps.shell.run_step(context)


def test_shell_sequence_with_ampersands_save_output():
    """Single shell command string with ampersands works."""
    context = Context({'one': 1,
                       'two': 2,
                       'three': 3,
                       'cmd': {
                           'run': 'echo {one} && echo {two} && echo {three}',
                           'save': True}
                       })
    pypyr.steps.shell.run_step(context)

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == ('1 \n2 \n3' if is_windows
                                        else '1\n2\n3')
    assert not context['cmdOut'].stderr


def test_shell_dict_input_with_string_interpolation_save_out():
    """Single command string works with string interpolation."""
    context = Context({'cmd': {'run': "echo blah",
                               'save': True}})
    pypyr.steps.shell.run_step(context)

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == 'blah'
    assert not context['cmdOut'].stderr


def test_shell_with_cwd():
    """Single command string works with string interpolation."""
    cmd = get_cmd('pwd', 'echo %cd%')
    context = Context({'cmd': {'run': cmd,
                               'save': True,
                               'cwd': 'tests'}})
    pypyr.steps.shell.run_step(context)

    assert context['cmdOut'].returncode == 0
    assert Path(context['cmdOut'].stdout).samefile('tests')
    assert not context['cmdOut'].stderr


def test_shell_error_throws():
    """Shell process returning 1 should throw CalledProcessError."""
    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': 'exit 1'})
        pypyr.steps.shell.run_step(context)


def test_empty_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.shell.run_step(context)

    assert str(err_info.value) == ("context['cmd'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.shell.")
