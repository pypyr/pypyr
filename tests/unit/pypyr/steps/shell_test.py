"""shell.py unit tests."""
import pypyr.steps.shell
import pytest
import subprocess


def test_shell_single_word():
    """One word shell command works."""
    context = {'cmd': 'date'}
    context = pypyr.steps.shell.run_step(context)


def test_shell_sequence():
    """Sequence of shell commands work."""
    context = {'cmd': 'touch deleteme.arb'}
    context = pypyr.steps.shell.run_step(context)

    context = {'cmd': 'ls deleteme.arb'}
    context = pypyr.steps.shell.run_step(context)

    context = {'cmd': 'rm -f deleteme.arb'}
    context = pypyr.steps.shell.run_step(context)


def test_shell_sequence_with_semicolons():
    """Single shell command string with semi-colons works."""
    context = {'cmd':
               'touch deleteme.arb; ls deleteme.arb; rm -f deleteme.arb;'}
    context = pypyr.steps.shell.run_step(context)


def test_shell_sequence_with_ampersands():
    """Single shell command string with ampersands works."""
    context = {'cmd':
               'touch deleteme.arb && ls deleteme.arb && rm -f deleteme.arb'}
    context = pypyr.steps.shell.run_step(context)


def test_shell_error_throws():
    """Shell process returning 1 should throw CalledProcessError"""
    with pytest.raises(subprocess.CalledProcessError):
        context = {'cmd': 'exit 1'}
        context = pypyr.steps.shell.run_step(context)


def test_empty_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(AssertionError):
        context = {'blah': 'blah blah'}
        context = pypyr.steps.shell.run_step(context)
