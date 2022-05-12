"""pypyr.steps.cmd unit tests.

For tests involving stdout & stderr set to files, see:
tests/integration/pypyr/steps/cmd_int_test.py
"""
from pathlib import Path
import subprocess

import pytest

from pypyr.config import config
from pypyr.context import Context
from pypyr.errors import ContextError, KeyNotInContextError
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

    # dict like accessors only here for backwards compatibility
    assert context['cmdOut']['returncode'] == 0
    assert context['cmdOut']['stdout'] == 'blah'
    assert not context['cmdOut']['stderr']

    assert context['cmdOut'].returncode == 0
    assert context['cmdOut'].stdout == 'blah'
    assert not context['cmdOut'].stderr


def test_cmd_dict_input_sequence_with_cwd():
    """Single command string works with cwd."""
    cmd = get_cmd('pwd', str(cmd_path.joinpath('pwd.bat')))

    context = Context({'fileName': 'deleteinterpolatedme.arb',
                       'cmd': {'run': cmd,
                               'save': True,
                               'cwd': 'tests'}})
    pypyr.steps.cmd.run_step(context)

    assert context['cmdOut'].returncode == 0
    assert Path(context['cmdOut'].stdout).samefile('./tests')
    assert not context['cmdOut'].stderr


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

    assert context['cmdOut'].returncode == 0
    assert Path(context['cmdOut'].stdout).samefile('./tests')
    assert not context['cmdOut'].stderr


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

    assert context['cmdOut'].returncode == 1
    assert not context['cmdOut'].stdout
    assert context['cmdOut'].stderr == 'arb err here'


def test_cmd_context_cmd_throw():
    """Empty cmd in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.cmd.run_step(context)

    assert str(err_info.value) == ("context['cmd'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.cmd.")


def test_cmd_run_save_with_stdout_stderr():
    """Raise err when setting stdout | stderr alongside save."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two three',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2],
            'save': True,
            'stdout': '/arb1',
            'stderr': '/arb2'}
    })

    with pytest.raises(ContextError) as err:
        pypyr.steps.cmd.run_step(context)

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")


def test_cmd_run_save_with_stdout_or_stderr():
    """Raise err when setting stdout | stderr alongside save - or not and."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two three',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2],
            'save': True,
            'stderr': '/arb2'}
    })

    with pytest.raises(ContextError) as err:
        pypyr.steps.cmd.run_step(context)

    assert str(err.value) == (
        "You can't set `stdout` or `stderr` when `save` is True.")


def test_cmd_error_throws_with_save_true_executable_not_found():
    """Raise error when can't find the subprocess executable."""
    cmd = get_cmd('tests/testfiles/cmds/xxx',
                  r'tests\testfiles\cmds\xxx')

    with pytest.raises(FileNotFoundError) as err:
        context = Context({'cmd': {'run': cmd, 'save': True}})
        pypyr.steps.cmd.run_step(context)

    # cmdOut NOT populated because couldn't run subproc at all.
    assert 'cmdOut' not in context

    # on windows, FileNotFoundError does NOT set filename, instead:
    # FileNotFoundError(2, 'The system cannot find the file specified',
    #                   None, 2 None)
    if not is_windows:
        err.value.filename == cmd

# region list input


def test_cmd_run_has_list_input_with_complex_args():
    """List input to run complex dict works with multiple args."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': {
                           'run': [
                               '{d} {a} "{b}" {c}',
                               '{e} four "five six" seven'],
                            'save': False}
                       })
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_list_input_with_simple_cmd_strings():
    """List input with command string works with multiple args."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': [
                           '{d} {a} "{b}" {c}',
                           '{e} four "five six" seven']})
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_list_input_with_complex_args():
    """List input mixing command string & dict works with multiple args."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'one',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': [
                           {'run': '{d} {a} "{b}" {c}',
                            'save': False},
                           '{e} four "five six" seven']})
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


def test_cmd_list_input_with_simple_cmd_strings_error_on_first():
    """List input with command string works stops on 1st error."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('echo blah',
                   r'tests\testfiles\cmds\echo.bat blah')

    context = Context({'a': 'WRONG VALUE',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': [
                           '{d} {a} "{b}" {c}',
                           '{e}']})

    with pytest.raises(subprocess.CalledProcessError) as err:
        pypyr.steps.cmd.run_step(context)

    if is_windows:
        assert err.value.cmd == f'{cmd1} WRONG VALUE "two two" three'
    else:
        assert err.value.cmd == [cmd1, 'WRONG', 'VALUE', 'two two', 'three']
    assert 'cmdOut' not in context


def test_cmd_run_has_list_input_with_complex_args_error_on_first():
    """List input to run complex dict works with error on first."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'WRONG',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': {
                           'run': [
                               '{d} {a} "{b}" {c}',
                               '{e} four "five six" seven'],
                            'save': False}
                       })

    with pytest.raises(subprocess.CalledProcessError) as err:
        pypyr.steps.cmd.run_step(context)

    if is_windows:
        assert err.value.cmd == f'{cmd1} WRONG "two two" three'
    else:
        assert err.value.cmd == [cmd1, 'WRONG', 'two two', 'three']
    assert 'cmdOut' not in context


def test_cmd_list_input_with_complex_args_error_on_first():
    """List input mixing command string & dict stops on 1st."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'WRONG',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': [
                           {'run': '{d} {a} "{b}" {c}',
                            'save': False},
                           '{e} four "five six" seven']})

    with pytest.raises(subprocess.CalledProcessError) as err:
        pypyr.steps.cmd.run_step(context)

    if is_windows:
        assert err.value.cmd == f'{cmd1} WRONG "two two" three'
    else:
        assert err.value.cmd == [cmd1, 'WRONG', 'two two', 'three']
    assert 'cmdOut' not in context


def test_cmd_list_input_with_complex_args_error_on_first_save():
    """List input mixing command string & dict stops on 1st save output."""
    cmd1 = get_cmd('tests/testfiles/cmds/args.sh',
                   r'tests\testfiles\cmds\args.bat')

    cmd2 = get_cmd('tests/testfiles/cmds/args2.sh',
                   r'tests\testfiles\cmds\args2.bat')

    context = Context({'a': 'WRONG',
                       'b': 'two two',
                       'c': 'three',
                       'd': cmd1,
                       'e': cmd2,
                       'cmd': [
                           {'run': '{d} {a} "{b}" {c}',
                            'save': True},
                           '{e} WRONG "five six" seven']})

    with pytest.raises(subprocess.CalledProcessError) as err:
        pypyr.steps.cmd.run_step(context)

    if is_windows:
        assert err.value.cmd == f'{cmd1} WRONG "two two" three'
    else:
        assert err.value.cmd == [cmd1, 'WRONG', 'two two', 'three']
    out = context['cmdOut']
    assert out.returncode == 1
    assert out.stdout == ''
    assert out.stderr == 'assert failed'


def test_cmd_run_has_list_input_save():
    """List input to run complex dict save all output."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo "two three"',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2],
            'save': True}
    })
    pypyr.steps.cmd.run_step(context)

    out = context['cmdOut']
    assert len(out) == 2
    out1 = out[0]
    assert out1.returncode == 0
    assert out1.stdout == 'one'
    assert not out1.stderr

    out2 = out[1]
    assert out2.returncode == 0
    assert out2.stdout == 'two three'
    assert not out2.stderr


def test_cmd_run_has_list_and_run_with_list_save():
    """List input with run also a list, everything save to results."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two',
                   r'tests\testfiles\cmds\echo.bat two')

    cmd3 = get_cmd('echo three',
                   r'tests\testfiles\cmds\echo.bat three')

    cmd4 = get_cmd('echo four',
                   r'tests\testfiles\cmds\echo.bat four')

    cmd5 = get_cmd('echo five',
                   r'tests\testfiles\cmds\echo.bat five')

    context = Context({
        'cmd': [
            {'run': [cmd1, cmd2],
             'save': True},
            {'run': [cmd3, cmd4],
             'save': True},
            cmd5,
        ]
    })
    pypyr.steps.cmd.run_step(context)

    out = context['cmdOut']
    assert len(out) == 4

    out1 = out[0]
    assert out1.returncode == 0
    assert out1.stdout == 'one'
    assert not out1.stderr

    out2 = out[1]
    assert out2.returncode == 0
    assert out2.stdout == 'two'
    assert not out2.stderr

    out3 = out[2]
    assert out3.returncode == 0
    assert out3.stdout == 'three'
    assert not out3.stderr

    out4 = out[3]
    assert out4.returncode == 0
    assert out4.stdout == 'four'
    assert not out4.stderr


def test_cmd_run_has_list_input_save_dev_null():
    """List input to run complex dict save all output to /dev/null."""
    cmd1 = get_cmd('echo one',
                   r'tests\testfiles\cmds\echo.bat one')

    cmd2 = get_cmd('echo two three',
                   r'tests\testfiles\cmds\echo.bat "two three"')

    context = Context({
        'cmd': {
            'run': [cmd1, cmd2],
            'stdout': '/dev/null',
            'stderr': '/dev/null'}
    })
    pypyr.steps.cmd.run_step(context)

    assert 'cmdOut' not in context


# endregion list input

# region encoding

powershell = "powershell -ExecutionPolicy Bypass -NoLogo -NoProfile"


def test_cmd_run_save_with_encoding():
    """Encoding works."""
    if is_windows:
        cmd = f"{powershell} ./tests/testfiles/cmds/bytes-out.ps1"
        encoding = 'utf-16le'
    else:
        cmd = 'tests/testfiles/cmds/bytes-out.sh'
        encoding = 'utf-16'

    context = Context({
        'cmd': {
            'run': cmd,
            'save': True,
            'encoding': encoding}
    })
    pypyr.steps.cmd.run_step(context)

    out = context['cmdOut']
    assert out.returncode == 0
    assert out.stdout == 'one two three'
    assert out.stderr == 'four'


def test_cmd_run_save_with_binary_mode():
    """Binary mode does not strip lf."""
    if is_windows:
        # the literal \ escaping the " is NB
        ps_cmd = """\
$out=[System.Text.Encoding]::Unicode.GetBytes(\\"one`n\\");
[System.Console]::OpenStandardOutput().Write($out, 0, $out.Length);
$err=[System.Text.Encoding]::Unicode.GetBytes(\\"two`n\\");
[System.Console]::OpenStandardError().Write($err, 0, $err.Length);"""

        cmd = f'powershell -NoLogo -NoProfile -Command {ps_cmd}'
    else:
        cmd = 'tests/testfiles/cmds/bytes-out-lf.sh'

    context = Context({
        'cmd': {
            'run': cmd,
            'save': True,
            'bytes': True}
    })
    pypyr.steps.cmd.run_step(context)

    out = context['cmdOut']
    assert out.returncode == 0
    assert out.stdout.decode('utf-16') == 'one\n'
    assert out.stderr.decode('utf-16') == 'two\n'

# endregion encoding
