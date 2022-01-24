"""Unit tests for pypyr/platform.py."""
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pypyr import platform

HOME = Path.home()

# region PlatformPaths
cu = Path('/cu')
cc = Path('/cc')
du = Path('/du')
dc = Path('/dc')


def test_to_str_no_offset():
    """Str with zero offset."""
    pp = platform.PlatformPaths(config_user=cu,
                                config_common=[cc],
                                data_dir_user=du,
                                data_dir_common=[dc])
    assert str(pp) == (f'config_user: {cu}\n'
                       'config_common:\n'
                       f'  - {cc}\n'
                       f'data_dir_user: {du}\n'
                       'data_dir_common:\n'
                       f'  - {dc}\n'
                       )


def test_to_str_offset_2():
    """Str with offset 2."""
    pp = platform.PlatformPaths(config_user=cu,
                                config_common=[cc],
                                data_dir_user=du,
                                data_dir_common=[dc])
    assert pp.to_str(2) == (f'  config_user: {cu}\n'
                            '  config_common:\n'
                            f'    - {cc}\n'
                            f'  data_dir_user: {du}\n'
                            '  data_dir_common:\n'
                            f'    - {dc}\n'
                            )


def test_to_str_offset_3():
    """Str with offset 3."""
    cc2 = Path('cc2')
    pp = platform.PlatformPaths(config_user=cu,
                                config_common=[cc, cc2],
                                data_dir_user=du,
                                data_dir_common=[dc])
    assert pp.to_str(3) == (f'   config_user: {cu}\n'
                            '   config_common:\n'
                            f'     - {cc}\n'
                            f'     - {cc2}\n'
                            f'   data_dir_user: {du}\n'
                            '   data_dir_common:\n'
                            f'     - {dc}\n'
                            )

# endregion PlatformPaths

# region fixtures


@pytest.fixture
def no_xdg_envs(monkeypatch):
    """Unset XDG env vars."""
    monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)
    monkeypatch.delenv('XDG_CONFIG_DIRS', raising=False)
    monkeypatch.delenv('XDG_DATA_HOME', raising=False)
    monkeypatch.delenv('XDG_DATA_DIRS', raising=False)


@pytest.fixture
def xdg_envs(monkeypatch):
    """Set XDG env vars."""
    monkeypatch.setenv('XDG_CONFIG_HOME', '/ch/')
    monkeypatch.setenv('XDG_CONFIG_DIRS', f'/cc{os.pathsep}/cc2')
    monkeypatch.setenv('XDG_DATA_HOME', '/dh')
    monkeypatch.setenv('XDG_DATA_DIRS', f'/dc/{os.pathsep}/dc2')


@pytest.fixture
def xdg_env_single(monkeypatch):
    """Set XDG env vars with single paths in the DIRS arrays."""
    monkeypatch.setenv('XDG_CONFIG_HOME', '/ch/')
    monkeypatch.setenv('XDG_CONFIG_DIRS', '/cc')
    monkeypatch.setenv('XDG_DATA_HOME', '/dh')
    monkeypatch.setenv('XDG_DATA_DIRS', '/dc/')


@pytest.fixture
def not_android(monkeypatch):
    """Unset Android $ENVs."""
    monkeypatch.delenv('ANDROID_DATA', raising=False)
    monkeypatch.delenv('ANDROID_ROOT', raising=False)


@pytest.fixture()
def env_android(monkeypatch):
    """Set $ENVs and path separator to mimic Android environment."""
    monkeypatch.setenv('ANDROID_DATA', '/data')
    monkeypatch.setenv('ANDROID_ROOT', '/system')
    monkeypatch.setattr('pypyr.platform.os.pathsep', ':')


@pytest.fixture()
def env_android_halfway(monkeypatch):
    """Set $ENVs to mimic half of the $ENVs for Android."""
    monkeypatch.setenv('ANDROID_DATA', '/data')
    monkeypatch.setenv('ANDROID_ROOT', '/arbxyzsdkskd')


@pytest.fixture
def windows(monkeypatch, not_android):
    """Set windows $ENV and pathsep."""
    monkeypatch.setenv('ALLUSERSPROFILE', 'C:/ProgramData1')
    monkeypatch.setattr('pypyr.platform.os.pathsep', ';')
    monkeypatch.setattr('pypyr.platform.sys.platform', 'win32')


@pytest.fixture
def posix(monkeypatch, no_win, not_android):
    """Set path separator to colon."""
    monkeypatch.setattr('pypyr.platform.os.pathsep', ':')


@pytest.fixture
def linux(monkeypatch, posix):
    """Set platform str to linux."""
    monkeypatch.setattr('pypyr.platform.sys.platform', 'linux')


@pytest.fixture
def cygwin(monkeypatch, posix):
    """Set platform str to cygwin."""
    monkeypatch.setattr('pypyr.platform.sys.platform', 'cygwin')


@pytest.fixture
def freebsd(monkeypatch, posix):
    """Set platform str to cygwin."""
    monkeypatch.setattr('pypyr.platform.sys.platform', 'freebsd')


@pytest.fixture
def darwin(monkeypatch, posix):
    """Set platform str to darwin."""
    monkeypatch.setattr('pypyr.platform.sys.platform', 'darwin')


@pytest.fixture
def no_win(monkeypatch):
    """Unset Windows ALLUSERSPROFILE environment variable."""
    monkeypatch.delenv('ALLUSERSPROFILE', raising=False)

# endregion

# region Xdg


def test_xdg_defaults(linux, no_xdg_envs):
    """Xdg with no $ENV set."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path(HOME, '.config/pypyr/config.yaml'),
        config_common=[Path('/etc/xdg/pypyr/config.yaml')],
        data_dir_user=Path(HOME, '.local/share/pypyr'),
        data_dir_common=[Path('/usr/local/share/pypyr'),
                         Path('/usr/share/pypyr')])


def test_xdg_vars_set(cygwin, xdg_envs):
    """Xdg with all $ENV set."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path('/ch//pypyr/config.yaml'),
        config_common=[Path('/cc/pypyr/config.yaml'),
                       Path('/cc2/pypyr/config.yaml')],
        data_dir_user=Path('/dh/pypyr'),
        data_dir_common=[Path('/dc/pypyr'),
                         Path('/dc2/pypyr')])


def test_xdg_vars_set_single(freebsd, xdg_env_single):
    """Xdg with all $ENV set and list values only have single values."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path('/ch//pypyr/config.yaml'),
        config_common=[Path('/cc/pypyr/config.yaml')],
        data_dir_user=Path('/dh/pypyr'),
        data_dir_common=[Path('/dc/pypyr')])

# endregion Xdg

# region MacOs


def test_mac_defaults(darwin, no_xdg_envs):
    """Mac with no xdg $ENV set."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path(HOME, '.config/pypyr/config.yaml'),
        config_common=[Path('/Library/Application Support/pypyr/config.yaml')],
        data_dir_user=Path(HOME, '.local/share/pypyr'),
        data_dir_common=[Path('/Library/Application Support/pypyr')])


def test_mac_vars_set(darwin, xdg_envs):
    """Xdg on Mac with all $ENV set."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path('/ch//pypyr/config.yaml'),
        config_common=[Path('/cc/pypyr/config.yaml'),
                       Path('/cc2/pypyr/config.yaml')],
        data_dir_user=Path('/dh/pypyr'),
        data_dir_common=[Path('/dc/pypyr'),
                         Path('/dc2/pypyr')])

# endregion MacOs

# region Windows


def test_win_defaults(windows, no_xdg_envs):
    """Windows with no xdg $ENV set."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path(HOME, '.config/pypyr/config.yaml'),
        config_common=[Path('C:/ProgramData1/pypyr/config.yaml')],
        data_dir_user=Path(HOME, '.local/share/pypyr'),
        data_dir_common=[Path('C:/ProgramData1/pypyr/')])


def test_win_allusersprofile_not_set(windows, no_win, no_xdg_envs):
    """Raise error when $ALLUSERSPROFILE is not set on Windows."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')
    assert pp == platform.PlatformPaths(
        config_user=Path(HOME, '.config/pypyr/config.yaml'),
        config_common=[Path('C:/ProgramData/pypyr/config.yaml')],
        data_dir_user=Path(HOME, '.local/share/pypyr'),
        data_dir_common=[Path('C:/ProgramData/pypyr/')])


def test_win_vars_set(windows, xdg_envs):
    """Win with all xdg $ENV set."""
    pp = platform.get_platform_paths('pypyr', 'config.yaml')

    assert pp == platform.PlatformPaths(
        config_user=Path('/ch//pypyr/config.yaml'),
        config_common=[Path('/cc/pypyr/config.yaml'),
                       Path('/cc2/pypyr/config.yaml')],
        data_dir_user=Path('/dh/pypyr'),
        data_dir_common=[Path('/dc/pypyr'),
                         Path('/dc2/pypyr')])
# endregion Windows

# region android


def get_jnius_mock():
    """Create a jnius mock that return path /arb."""
    mock_jnius = Mock()
    mock_autoclass = Mock()
    mock_get_abs_path = Mock(return_value='/arb')
    mock_get_parent = Mock()
    mock_get_parent.return_value.getAbsolutePath = mock_get_abs_path
    mock_get_files_dir = Mock()
    mock_get_files_dir.return_value.getParentFile = mock_get_parent

    mock_autoclass.return_value.getFilesDir = mock_get_files_dir

    mock_jnius.autoclass = mock_autoclass
    return mock_jnius


def test_android_defaults(env_android):
    """Android with jnius success path."""
    mock_jnius = get_jnius_mock()

    with patch.dict('sys.modules', {'jnius': mock_jnius}):
        pp = platform.get_platform_paths('pypyr', 'config.yaml')

    mock_jnius.autoclass.assert_called_once_with('android.content.Context')

    assert pp == platform.PlatformPaths(
        config_user=Path('/arb/shared_prefs/pypyr/config.yaml'),
        config_common=[Path('/arb/shared_prefs/pypyr/config.yaml')],
        data_dir_user=Path('/arb/files/pypyr'),
        data_dir_common=[Path('/arb/files/pypyr')])


@patch('pypyr.platform.sys')
def test_android_not_found(mock_sys, env_android):
    """Android with jnius failed import."""
    mock_jnius = get_jnius_mock()
    mock_jnius.autoclass.side_effect = ModuleNotFoundError()

    mock_sys.path = ['/arb', '/hello']
    with patch.dict('sys.modules', {'jnius': mock_jnius}):
        with pytest.raises(OSError) as err:
            platform.get_platform_paths('pypyr', 'config.yaml')

    assert str(err.value) == "Cannot find path to android app folder"
    mock_jnius.autoclass.assert_called_once_with('android.content.Context')


@patch('pypyr.platform.sys')
def test_android_via_sys_path(mock_sys, env_android):
    """Android with jnius failed import finds dir via sys.path."""
    mock_jnius = get_jnius_mock()
    mock_jnius.autoclass.side_effect = ModuleNotFoundError()

    mock_sys.path = ['/arb', '/data/user/1/a/files']
    with patch.dict('sys.modules', {'jnius': mock_jnius}):
        pp = platform.get_platform_paths('pypyr', 'config.yaml')

    mock_jnius.autoclass.assert_called_once_with('android.content.Context')

    assert pp == platform.PlatformPaths(
        config_user=Path('/data/user/1/a/shared_prefs/pypyr/config.yaml'),
        config_common=[Path('/data/user/1/a/shared_prefs/pypyr/config.yaml')],
        data_dir_user=Path('/data/user/1/a/files/pypyr'),
        data_dir_common=[Path('/data/user/1/a/files/pypyr')])


@patch('pypyr.platform.sys')
def test_android_halfway(mock_sys, env_android_halfway):
    """Android has to have both envs matching to pass."""
    mock_sys.platform = 'win32'
    assert platform.get_platform_dir_finder() is platform.Windows

# endregion android
