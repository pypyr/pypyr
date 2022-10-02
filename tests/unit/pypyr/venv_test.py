"""Unit tests for subproc.py."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, call
import sys

import pytest

from pypyr.errors import Error, ContextError
from pypyr.venv import EnvBuilderWithExtraDeps, VenvCreator

IS_AFTER_PY_3_9 = sys.version_info >= (3, 9)

# region VenvCreator


def get_simple_context():
    """Create a test SimpleNamespace to serve as EnvBuilder context."""
    context = SimpleNamespace()
    context.env_exec_cmd = '/python'
    context.bin_path = '/venv/bin'
    context.env_dir = '/venv'
    return context


@patch('pypyr.venv.VenvCreator.DEFAULT_USE_SYMLINKS', new=True)
def test_venv_creator_minimal_posix():
    """Create venv with minimal inputs on posix."""
    context = get_simple_context()
    with patch('pypyr.venv.EnvBuilderWithExtraDeps') as mock_builder:
        mock_builder.return_value.context = context
        vc = VenvCreator('/arb')
        vc.create()
        vc.install_dependencies()

    expected_path = str(Path('/arb').resolve())
    assert vc.DEFAULT_USE_SYMLINKS
    assert vc.path == expected_path
    assert vc.pip_extras is None
    assert vc.upgrade_pip
    assert vc._is_done
    assert vc._future is None
    mock_builder.assert_called_once_with(system_site_packages=False,
                                         clear=False,
                                         symlinks=True,
                                         upgrade=False,
                                         with_pip=True,
                                         prompt=None,
                                         upgrade_deps=False,
                                         is_quiet=False)
    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_called_once_with(context)
    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.VenvCreator.DEFAULT_USE_SYMLINKS', new=False)
def test_venv_creator_minimal_nt():
    """Create venv with minimal inputs on nt."""
    context = get_simple_context()
    with patch('pypyr.venv.EnvBuilderWithExtraDeps') as mock_builder:
        mock_builder.return_value.context = context
        vc = VenvCreator('/arb')
        vc.create()
        vc.install_dependencies()

    expected_path = str(Path('/arb').resolve())
    assert not vc.DEFAULT_USE_SYMLINKS
    assert vc.path == expected_path
    assert vc.pip_extras is None
    assert vc.upgrade_pip
    assert vc._is_done
    assert vc._future is None
    mock_builder.assert_called_once_with(system_site_packages=False,
                                         clear=False,
                                         symlinks=False,
                                         upgrade=False,
                                         with_pip=True,
                                         prompt=None,
                                         upgrade_deps=False,
                                         is_quiet=False)

    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_called_once_with(context)
    mocked_builder.pip_install_extras.assert_not_called()


def test_venv_creator_from_mapping_minimal():
    """Create venv with minimal inputs from mapping."""
    d = {'path': '~/arb'}
    resolved_path = str(Path('~/arb').expanduser().resolve())

    context = get_simple_context()
    with patch('pypyr.venv.EnvBuilderWithExtraDeps') as mock_builder:
        mock_builder.return_value.context = context
        vcs = list(VenvCreator.from_mapping(d))
        assert len(vcs) == 1
        vc = vcs[0]
        vc.create()
        vc.install_dependencies()

    assert vc.path == resolved_path
    assert vc.pip_extras is None
    assert vc.upgrade_pip
    assert vc._is_done
    assert vc._future is None
    mock_builder.assert_called_once_with(
        system_site_packages=False,
        clear=False,
        symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False,
        with_pip=True,
        prompt=None,
        upgrade_deps=False,
        is_quiet=False)

    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(resolved_path)
    mocked_builder.upgrade_dependencies.assert_called_once_with(context)
    mocked_builder.pip_install_extras.assert_not_called()


def test_venv_creator_from_mapping_minimal_list():
    """Create venv with minimal inputs from mapping with list of paths."""
    d = {'path': ['/arb1', '/arb2']}
    context = get_simple_context()
    with patch('pypyr.venv.EnvBuilderWithExtraDeps') as mock_builder:
        mock_builder.return_value.context = context
        vcs = list(VenvCreator.from_mapping(d))
        assert len(vcs) == 2
        vc0 = vcs[0]
        vc0.create()
        vc0.install_dependencies()

        vc1 = vcs[1]
        vc1.create()
        vc1.install_dependencies()

    expected_path1 = str(Path('/arb1').resolve())
    expected_path2 = str(Path('/arb2').resolve())
    assert vc0.path == expected_path1
    assert vc0.pip_extras is None
    assert vc0.upgrade_pip
    assert vc0._is_done
    assert vc0._future is None

    assert vc1.path == expected_path2
    assert vc1.pip_extras is None
    assert vc0.upgrade_pip
    assert vc1._is_done
    assert vc1._future is None

    assert mock_builder.call_count == 2
    assert mock_builder.mock_calls[0] == call(
        system_site_packages=False,
        clear=False, symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False, with_pip=True,
        prompt=None, upgrade_deps=False,
        is_quiet=False)

    assert mock_builder.mock_calls[1] == call(
        system_site_packages=False,
        clear=False, symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False, with_pip=True,
        prompt=None, upgrade_deps=False,
        is_quiet=False)

    mocked_builder = mock_builder.return_value
    assert mocked_builder.create.call_count == 2
    assert mocked_builder.create.mock_calls[0] == call(expected_path1)
    assert mocked_builder.create.mock_calls[1] == call(expected_path2)

    assert mocked_builder.upgrade_dependencies.call_count == 2
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)

    mocked_builder.pip_install_extras.assert_not_called()


def test_venv_creator_from_mapping_maximal():
    """Create venv with maximal inputs from mapping."""
    d = {
        'path': '/arb',
        'system_site_packages': True,
        'clear': False,
        'symlinks': True,
        'upgrade': True,
        'with_pip': True,
        'prompt': 'arbprompt',
        'upgrade_pip': False,
        'pip': 'package1 package2',
        'quiet': True
    }

    context = get_simple_context()

    with patch('pypyr.venv.EnvBuilderWithExtraDeps') as mock_builder:
        mock_builder.return_value.context = context
        vcs = list(VenvCreator.from_mapping(d))
        assert len(vcs) == 1
        vc = vcs[0]
        vc.create()
        vc.install_dependencies()

    expected_path = str(Path('/arb').resolve())
    assert vc.path == expected_path
    assert vc.pip_extras == 'package1 package2'
    assert not vc.upgrade_pip
    assert vc._is_done
    assert vc._future is None
    mock_builder.assert_called_once_with(system_site_packages=True,
                                         clear=False,
                                         symlinks=True,
                                         upgrade=True,
                                         with_pip=True,
                                         prompt='arbprompt',
                                         upgrade_deps=False,
                                         is_quiet=True)

    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()
    mocked_builder.pip_install_extras.assert_called_once_with(
        'package1 package2')


def test_venv_creator_from_mapping_maximal_no_pip():
    """Create venv with maximal inputs from mapping when with_pip False."""
    d = {
        'path': '/arb',
        'system_site_packages': True,
        'clear': False,
        'symlinks': True,
        'upgrade': True,
        'with_pip': False,
        'prompt': 'arbprompt',
        'upgrade_pip': False,
        'quiet': True
    }

    context = get_simple_context()

    with patch('pypyr.venv.EnvBuilderWithExtraDeps') as mock_builder:
        mock_builder.return_value.context = context
        vcs = list(VenvCreator.from_mapping(d))
        assert len(vcs) == 1
        vc = vcs[0]
        vc.create()
        vc.install_dependencies()

    expected_path = str(Path('/arb').resolve())
    assert vc.path == expected_path
    assert vc.pip_extras is None
    assert not vc.upgrade_pip
    assert vc._is_done
    assert vc._future is None
    mock_builder.assert_called_once_with(system_site_packages=True,
                                         clear=False,
                                         symlinks=True,
                                         upgrade=True,
                                         with_pip=False,
                                         prompt='arbprompt',
                                         upgrade_deps=False,
                                         is_quiet=True)

    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()
    mocked_builder.pip_install_extras.assert_not_called()


def test_venv_creator_from_mapping_no_path_error():
    """Raise error when instantiate from mapping with no path."""
    with pytest.raises(ContextError) as err:
        next(VenvCreator.from_mapping({'a': 'b'}))

    assert str(err.value) == (
        "path is mandatory on mapping input for venv create.")


def test_venv_creator_from_mapping_path_not_string_not_list():
    """Raise error when instantiate from mapping with path wrong type."""
    with pytest.raises(ContextError) as err:
        next(VenvCreator.from_mapping({'path': 123}))

    assert str(err.value) == (
        "venv.path input should be a string or list. "
        + "Current input is: 123")


def test_venv_creator_error_upgrade_and_clear():
    """Raise error when upgrade and clear true."""
    with pytest.raises(ContextError) as err:
        VenvCreator('/arb', upgrade=True, clear=True)

    assert str(err.value) == VenvCreator.EXCEPTION_UPGRADE_CLEAR.format(
        path='/arb')


def test_venv_creator_no_pip_sets_upgrade_pip_false():
    """Set upgrade_pip False when with_pip is False."""
    vc = VenvCreator('/arb', with_pip=False)
    assert not vc.with_pip
    assert not vc.upgrade_pip

    vc = VenvCreator('/arb', with_pip=False, upgrade_pip=True)
    assert not vc.with_pip
    assert not vc.upgrade_pip


def test_venv_creator_error_no_pip_with_extras():
    """Raise error when with_pip false and pip_extras or upgrade_pip set."""
    with pytest.raises(ContextError) as err:
        VenvCreator('/arb', with_pip=False, pip_extras="package1 package2")

    assert str(err.value) == VenvCreator.EXCEPTION_NO_PIP.format(path='/arb')


def test_venv_creator_error_install_deps_before_create():
    """Raise error when install dependencies before create."""
    vc = VenvCreator('/arb')

    with pytest.raises(Error) as err:
        vc.install_dependencies()

    expected_path = str(Path('/arb').resolve())
    assert str(err.value) == (
        "you can't call install_dependencies before the environment "
        + f"is installed successfully for {expected_path}.")


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_creator_error_install_deps_with_pip_false(mock_builder):
    """Raise error when install dependencies when with_pip is false."""
    vc = VenvCreator('/arb', with_pip=False)
    context = get_simple_context()

    with pytest.raises(Error) as err:
        mock_builder.return_value.with_pip = False
        mock_builder.return_value.context = context
        vc.create()
        vc.install_dependencies()

    expected_path = str(Path('/arb').resolve())
    assert str(err.value) == (
        f"you can't install extra dependencies into {expected_path} because "
        + "with_pip is False.")

    mock_builder.assert_called_once_with(
        system_site_packages=False,
        clear=False,
        symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False,
        with_pip=False,
        prompt=None,
        upgrade_deps=False,
        is_quiet=False)

    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()


def test_venv_creator_error_check_result_no_executor():
    """Raise error when check_result without create_in_executor.."""
    vc = VenvCreator('/arb')

    with pytest.raises(Error) as err:
        vc.check_result()

    expected_path = str(Path('/arb').resolve())
    assert str(err.value) == (
        "You can only call check_result after create_in_executor. "
        + f"Error creating venv {expected_path}")


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_creator_in_executor(mock_builder):
    """Create venv in executor."""
    vc = VenvCreator('/arb')
    with ThreadPoolExecutor() as executor:
        vc.create_in_executor(executor)

    assert not vc.check_result()

    mock_builder.assert_called_once_with(
        system_site_packages=False,
        clear=False,
        symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False,
        with_pip=True,
        prompt=None,
        upgrade_deps=False,
        is_quiet=False)

    expected_path = str(Path('/arb').resolve())

    mocked_builder = mock_builder.return_value
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_creator_in_executor_raises(mock_builder):
    """Create venv in executor where create raises error."""
    vc = VenvCreator('/arb')
    mocked_builder = mock_builder.return_value
    mocked_builder.create.side_effect = ValueError('arb')

    with ThreadPoolExecutor() as executor:
        vc.create_in_executor(executor)

    assert repr(vc.check_result()) == repr(ValueError('arb'))

    mock_builder.assert_called_once_with(
        system_site_packages=False,
        clear=False,
        symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False,
        with_pip=True,
        prompt=None,
        upgrade_deps=False,
        is_quiet=False)

    expected_path = str(Path('/arb').resolve())
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_creator_in_executor_raises_base_exception(mock_builder):
    """Create venv in executor where create raises KeyBoardInterrupt."""
    vc = VenvCreator('/arb')
    mocked_builder = mock_builder.return_value
    mocked_builder.create.side_effect = KeyboardInterrupt()

    with ThreadPoolExecutor() as executor:
        vc.create_in_executor(executor)

    with pytest.raises(KeyboardInterrupt):
        vc.check_result()

    mock_builder.assert_called_once_with(
        system_site_packages=False,
        clear=False,
        symlinks=VenvCreator.DEFAULT_USE_SYMLINKS,
        upgrade=False,
        with_pip=True,
        prompt=None,
        upgrade_deps=False,
        is_quiet=False)

    expected_path = str(Path('/arb').resolve())
    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()
# endregion VenvCreator

# region EnvBuilderWithContext


def test_env_builder_minimal():
    """Instantiate env builder with minimal args."""
    eb = EnvBuilderWithExtraDeps()
    assert not eb.is_quiet

    assert not eb.system_site_packages
    assert not eb.clear
    assert not eb.symlinks
    assert not eb.upgrade
    assert not eb.with_pip
    assert eb.prompt is None
    assert not eb.upgrade_deps


def test_env_builder_maximal():
    """Instantiate env builder with maximal args."""
    eb = EnvBuilderWithExtraDeps(system_site_packages=True,
                                 clear=True,
                                 symlinks=True,
                                 upgrade=False,
                                 with_pip=True,
                                 prompt='arbprompt',
                                 upgrade_deps=True,
                                 is_quiet=True)

    assert eb.is_quiet

    assert eb.system_site_packages
    assert eb.clear
    assert eb.symlinks
    assert not eb.upgrade
    assert eb.with_pip
    assert eb.prompt == 'arbprompt'
    assert eb.upgrade_deps


@patch('pypyr.venv.IS_BEFORE_PY_3_9', new=True)
def test_env_builder_maximal_before_py_3_9():
    """Instantiate env builder with maximal args before py 3.9."""
    with patch('pypyr.venv.EnvBuilder.__init__') as mock_builder:
        eb = EnvBuilderWithExtraDeps(system_site_packages=True,
                                     clear=True,
                                     symlinks=True,
                                     upgrade=False,
                                     with_pip=True,
                                     prompt='arbprompt',
                                     upgrade_deps=True,
                                     is_quiet=True)

    assert eb.is_quiet

    mock_builder.assert_called_once_with(system_site_packages=True,
                                         clear=True,
                                         symlinks=True,
                                         upgrade=False,
                                         with_pip=True,
                                         prompt='arbprompt')

    assert eb.upgrade_deps


@patch('pypyr.venv.IS_BEFORE_PY_3_9', new=False)
def test_env_builder_maximal_after_py_3_9():
    """Instantiate env builder with maximal args after py 3.9."""
    with patch('pypyr.venv.EnvBuilder.__init__') as mock_builder:
        eb = EnvBuilderWithExtraDeps(system_site_packages=True,
                                     clear=True,
                                     symlinks=True,
                                     upgrade=False,
                                     with_pip=True,
                                     prompt='arbprompt',
                                     upgrade_deps=True,
                                     is_quiet=True)

    assert eb.is_quiet

    mock_builder.assert_called_once_with(system_site_packages=True,
                                         clear=True,
                                         symlinks=True,
                                         upgrade=False,
                                         with_pip=True,
                                         prompt='arbprompt',
                                         upgrade_deps=True)


def test_env_builder_maximal_upgrade():
    """Instantiate env builder with maximal args and upgrade True."""
    eb = EnvBuilderWithExtraDeps(system_site_packages=True,
                                 clear=False,
                                 symlinks=True,
                                 upgrade=True,
                                 with_pip=True,
                                 prompt='arbprompt',
                                 upgrade_deps=True,
                                 is_quiet=True)

    assert eb.is_quiet

    assert eb.system_site_packages
    assert not eb.clear
    assert eb.symlinks
    assert eb.upgrade
    assert eb.with_pip
    assert eb.prompt == 'arbprompt'
    assert eb.upgrade_deps


@patch('pypyr.venv.subprocess.check_call')
def test_env_builder_upgrade_deps_no_quiet(mock_subproc_run):
    """Install dependencies without quiet mode."""
    eb = EnvBuilderWithExtraDeps()
    context = get_simple_context()

    eb.post_setup(context)
    eb.upgrade_dependencies(context)

    mock_subproc_run.assert_called_once_with(
        ['/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools'])


@patch('pypyr.venv.subprocess.check_call')
def test_env_builder_upgrade_deps_quiet(mock_subproc_run):
    """Install dependencies with quiet mode."""
    eb = EnvBuilderWithExtraDeps(is_quiet=True)
    context = get_simple_context()

    eb.post_setup(context)
    eb.upgrade_dependencies(context)

    mock_subproc_run.assert_called_once_with(
        ['/python', '-m', 'pip', 'install', '--upgrade', '-q',
         'pip', 'setuptools'])


@patch('pypyr.venv.subprocess.run')
def test_env_builder_install_pip_list_input(mock_subproc_run):
    """Install dependencies with list input rather than string."""
    eb = EnvBuilderWithExtraDeps()
    context = get_simple_context()

    eb.post_setup(context)
    eb.pip_install_extras(
        ['package1', 'package2==1.2.3', 'package3>=4.5.6,<7.8.9'])

    mock_subproc_run.assert_called_once_with(
        ['/python', '-m', 'pip', 'install',
         'package1', 'package2==1.2.3', 'package3>=4.5.6,<7.8.9'],
        check=True)


@patch('pypyr.venv.subprocess.run')
def test_env_builder_install_pip_extras(mock_subproc_run):
    """Install dependencies without quiet mode."""
    eb = EnvBuilderWithExtraDeps()
    context = get_simple_context()

    eb.post_setup(context)
    eb.pip_install_extras('package1 package2==1.2.3 package3>=4.5.6,<7.8.9')

    mock_subproc_run.assert_called_once_with(
        ['/python', '-m', 'pip', 'install',
         'package1', 'package2==1.2.3', 'package3>=4.5.6,<7.8.9'],
        check=True)


@patch('pypyr.venv.subprocess.run')
def test_env_builder_install_pip_extras_quiet(mock_subproc_run):
    """Install dependencies with quiet mode."""
    eb = EnvBuilderWithExtraDeps(is_quiet=True)
    context = get_simple_context()

    eb.post_setup(context)
    eb.pip_install_extras('package1 package2==1.2.3 package3>=4.5.6,<7.8.9')

    mock_subproc_run.assert_called_once_with(
        ['/python', '-m', 'pip', 'install', '-q',
         'package1', 'package2==1.2.3', 'package3>=4.5.6,<7.8.9'],
        check=True)

# endregion EnvBuilderWithContext
