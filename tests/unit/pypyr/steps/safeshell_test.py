"""safeshell.py unit tests."""
import platform
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.safeshell
import pytest
import subprocess


def test_shell_single_word():
    """One word shell command works."""
    context = Context({'cmd': 'date'})
    pypyr.steps.safeshell.run_step(context)


def test_shell_sequence():
    """Sequence of shell commands work."""
    context = Context({'cmd': 'touch deleteme.arb'})
    pypyr.steps.safeshell.run_step(context)

    context = Context({'cmd': 'ls deleteme.arb'})
    pypyr.steps.safeshell.run_step(context)

    context = Context({'cmd': 'rm -f deleteme.arb'})
    pypyr.steps.safeshell.run_step(context)


def test_shell_sequence_with_string_interpolation():
    """Single shell command string works with string interpolation."""
    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': 'touch {fileName}'})
    context = pypyr.steps.safeshell.run_step(context)

    context = Context({'cmd': 'ls deleteinterpolatedme.arb'})
    context = pypyr.steps.safeshell.run_step(context)

    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': 'rm -f {fileName}'})
    pypyr.steps.safeshell.run_step(context)


def test_shell_error_throws():
    """Shell process returning 1 should throw CalledProcessError"""
    cmd = '/bin/false' if platform.system() != 'Darwin' else '/usr/bin/false'
    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': cmd})
        context = pypyr.steps.safeshell.run_step(context)


def test_empty_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.safeshell.run_step(context)

    assert str(err_info.value) == ("context['cmd'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.cmd.")
