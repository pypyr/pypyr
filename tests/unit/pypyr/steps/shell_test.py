"""shell.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.shell
import pytest
import subprocess


def test_shell_single_word():
    """One word shell command works."""
    context = Context({'cmd': 'date'})
    pypyr.steps.shell.run_step(context)


def test_shell_sequence():
    """Sequence of shell commands work."""
    context = Context({'cmd': 'touch deleteme.arb'})
    pypyr.steps.shell.run_step(context)

    context = Context({'cmd': 'ls deleteme.arb'})
    pypyr.steps.shell.run_step(context)

    context = Context({'cmd': 'rm -f deleteme.arb'})
    pypyr.steps.shell.run_step(context)


def test_shell_sequence_with_semicolons():
    """Single shell command string with semi-colons works."""
    context = Context(
        {'cmd':
         'touch deleteme.arb; ls deleteme.arb; rm -f deleteme.arb;'})
    pypyr.steps.shell.run_step(context)


def test_shell_sequence_with_string_interpolation():
    """Single shell command string works with string interpolation."""
    context = Context(
        {'fileName': 'deleteme.arb',
         'cmd':
         'touch {fileName} && ls deleteme.arb && rm -f deleteme.arb;'})
    pypyr.steps.shell.run_step(context)


def test_shell_sequence_with_ampersands():
    """Single shell command string with ampersands works."""
    context = Context(
        {'cmd':
         'touch deleteme.arb && ls deleteme.arb && rm -f deleteme.arb'})
    pypyr.steps.shell.run_step(context)


def test_shell_error_throws():
    """Shell process returning 1 should throw CalledProcessError"""
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
