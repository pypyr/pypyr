"""cmd.py unit tests."""
from pathlib import Path
import platform
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.cmd
import pytest
import subprocess


def test_cmd_single_word():
    """One word command works."""
    context = Context({'cmd': 'date'})
    pypyr.steps.cmd.run_step(context)


def test_cmd_sequence():
    """Sequence of commands work."""
    context = Context({'cmd': 'touch deleteme.arb'})
    pypyr.steps.cmd.run_step(context)

    context = Context({'cmd': 'ls deleteme.arb'})
    pypyr.steps.cmd.run_step(context)

    context = Context({'cmd': 'rm -f deleteme.arb'})
    pypyr.steps.cmd.run_step(context)


def test_cmd_sequence_with_string_interpolation():
    """Single command string works with string interpolation."""
    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': 'touch {fileName}'})
    pypyr.steps.cmd.run_step(context)

    context = Context({'cmd': 'ls deleteinterpolatedme.arb'})
    pypyr.steps.cmd.run_step(context)

    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': 'rm -f {fileName}'})
    pypyr.steps.cmd.run_step(context)


def test_cmd_dict_input_sequence_with_string_interpolation():
    """Single command string works with string interpolation."""
    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': {'run': 'touch {fileName}'}})
    pypyr.steps.cmd.run_step(context)

    context = Context({'cmd': 'ls deleteinterpolatedme.arb'})
    pypyr.steps.cmd.run_step(context)

    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': 'rm -f {fileName}'})
    pypyr.steps.cmd.run_step(context)
    assert 'cmdOut' not in context


def test_cmd_dict_input_sequence_with_string_interpolation_save_out():
    """Single command string works with string interpolation."""
    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': {'run': 'echo blah',
                               'save': True}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 0
    assert context['cmdOut']['stdout'] == 'blah\n'
    assert not context['cmdOut']['stderr']


def test_cmd_dict_input_sequence_with_cwd():
    """Single command string works with cwd."""
    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': {'run': 'pwd',
                               'save': True,
                               'cwd': './tests'}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 0
    assert Path(context['cmdOut']['stdout'].rstrip('\n')).samefile('./tests')
    assert not context['cmdOut']['stderr']


def test_cmd_dict_input_sequence_with_cwd_interpolate():
    """Single command string works with cwd interpolation."""
    context = Context({'k1': './tests',
                       'cmd': {'run': 'pwd',
                               'save': True,
                               'cwd': '{k1}'}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 0
    assert Path(context['cmdOut']['stdout'].rstrip('\n')).samefile('./tests')
    assert not context['cmdOut']['stderr']


def test_cmd_error_throws():
    """Process returning 1 should throw CalledProcessError."""
    cmd = '/bin/false' if platform.system() != 'Darwin' else '/usr/bin/false'
    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': cmd})
        pypyr.steps.cmd.run_step(context)


def test_cmd_error_throws_with_save_true():
    """Process returning 1 should throw CalledProcessError."""
    cmd = '/bin/cat xblahx'
    with pytest.raises(subprocess.CalledProcessError):
        context = Context({'cmd': {'run': cmd, 'save': True}})
        pypyr.steps.cmd.run_step(context)

    assert context['cmdOut']['returncode'] == 1
    assert not context['cmdOut']['stdout']
    assert 'xblahx: No such file or directory\n' in context['cmdOut']['stderr']


def test_cmd_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.cmd.run_step(context)

    assert str(err_info.value) == ("context['cmd'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.cmd.")
