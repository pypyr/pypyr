"""safeshell.py unit tests."""
from pypyr.context import Context
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
    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': '/bin/false'})
        context = pypyr.steps.safeshell.run_step(context)


def test_empty_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(AssertionError):
        context = Context({'blah': 'blah blah'})
        pypyr.steps.safeshell.run_step(context)
