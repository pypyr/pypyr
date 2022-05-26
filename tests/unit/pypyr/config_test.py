"""Unit tests for pypyr/config.py."""
from pathlib import Path
import sys
from unittest.mock import call, mock_open, patch

import pytest

from pypyr.config import Config
from pypyr.errors import ConfigError
from pypyr.platform import PlatformPaths

CWD = Path.cwd()
current_platform = sys.platform
is_macos: bool = current_platform == 'darwin'
is_windows: bool = current_platform == 'win32'
is_posix: bool = not (is_macos or is_windows)


@pytest.fixture
def no_envs(monkeypatch):
    """Remove PYPYR_ env variables for test duration."""
    monkeypatch.delenv('PYPYR_CMD_ENCODING', raising=False)
    monkeypatch.delenv('PYPYR_ENCODING', raising=False)
    monkeypatch.delenv('PYPYR_SKIP_INIT', raising=False)
    monkeypatch.delenv('PYPYR_CONFIG_GLOBAL', raising=False)
    monkeypatch.delenv('PYPYR_CONFIG_LOCAL', raising=False)

# region default initialization


def test_config_defaults(no_envs):
    """Default config instance with all attributes as expected."""
    config = Config()
    assert config.config_loaded_paths == []
    assert config.cwd == CWD
    assert config.is_macos is is_macos
    assert config.is_posix is is_posix
    assert config.is_windows is is_windows
    assert config.platform == current_platform
    assert config.platform_paths is None
    assert config.pyproject_toml is None
    assert config.skip_init is False

    assert config.vars == {}
    assert config.shortcuts == {}

    assert config.json_ascii is False
    assert config.json_indent == 2
    assert config.pipelines_subdir == 'pipelines'
    assert config.log_config is None
    assert config.log_date_format == '%Y-%m-%d %H:%M:%S'
    assert config.log_notify_format == '%(message)s'
    assert config.log_detail_format == (
        '%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s')

    assert config.default_backoff == 'fixed'
    assert config.default_cmd_encoding is None
    assert config.default_encoding is None
    assert config.default_loader == 'pypyr.loaders.file'
    assert config.default_group == 'steps'
    assert config.default_success_group == 'on_success'
    assert config.default_failure_group == 'on_failure'


def test_config_with_encoding(monkeypatch, no_envs):
    """Set encoding via env variable."""
    monkeypatch.setenv('PYPYR_ENCODING', 'arb')
    monkeypatch.setenv('PYPYR_CMD_ENCODING', 'arb2')
    config = Config()
    config.default_encoding == 'arb'
    config.default_cmd_encoding == 'arb2'


def test_config_platforms(monkeypatch):
    """Boolean logic on which platform is correct for win vs mac vs posix."""
    monkeypatch.setattr('pypyr.platform.sys.platform', 'win32')

    config = Config()
    assert config.platform == 'win32'
    assert config.is_macos is False
    assert config.is_posix is False
    assert config.is_windows is True

    monkeypatch.setattr('pypyr.platform.sys.platform', 'linux')

    config = Config()
    assert config.platform == 'linux'
    assert config.is_macos is False
    assert config.is_posix is True
    assert config.is_windows is False

    monkeypatch.setattr('pypyr.platform.sys.platform', 'darwin')

    config = Config()
    assert config.platform == 'darwin'
    assert config.is_macos is True
    assert config.is_posix is False
    assert config.is_windows is False

    monkeypatch.setattr('pypyr.platform.sys.platform', 'cygwin')

    config = Config()
    assert config.platform == 'cygwin'
    assert config.is_macos is False
    assert config.is_posix is True
    assert config.is_windows is False

# endregion default initialization

# region init (heavy)


def test_config_skip_init(monkeypatch, no_envs):
    """Skip init when $PYPYR_SKIP_INIT true."""
    monkeypatch.setenv('PYPYR_SKIP_INIT', '1')
    config = Config()
    config.init()

    assert config.skip_init is True


fake_platform_paths = PlatformPaths(config_user=Path('/cu'),
                                    config_common=[Path('/cc')],
                                    data_dir_user=Path('/du'),
                                    data_dir_common=[Path('/dc')])


@patch('pypyr.platform.get_platform_paths', return_value=fake_platform_paths)
def test_config_init_no_files_found(mock_get_platform, no_envs):
    """Heavy init does not raise if no files found."""
    mock_opens = [
        OSError(),
        OSError(),
        OSError(),
        OSError()
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_group == 'steps'
    assert config.pyproject_toml is None
    assert config.config_loaded_paths == []
    assert config.platform_paths == fake_platform_paths

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


@patch('pypyr.platform.get_platform_paths')
def test_config_init_all_files_found(mock_get_platform, no_envs):
    """Heavy init merges all files."""
    f1 = mock_open(read_data='pipelines_subdir: arb1\ndefault_backoff: x')
    f2 = mock_open(read_data='pipelines_subdir: arb2\ndefault_loader: y')
    f3 = mock_open(read_data='pipelines_subdir: arb3\ndefault_group: z')
    f4 = mock_open(read_data=(
                   b'arbkey = 123\n'
                   b'[tool.pypyr]\n'
                   b'pipelines_subdir = "arb4"\n'
                   b'default_success_group = "dsg"'))
    f5 = mock_open(
        read_data='pipelines_subdir: arb5\ndefault_failure_group: dsf')

    mock_opens = [
        f1.return_value,
        f2.return_value,
        f3.return_value,
        f4.return_value,
        f5.return_value
    ]

    fake_pp_multiple_common = PlatformPaths(
        config_user=Path('/cu'),
        config_common=[Path('/cc1'), Path('/cc2')],
        data_dir_user=Path('/du'),
        data_dir_common=[Path('/dc')])

    mock_get_platform.return_value = fake_pp_multiple_common

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'arb5'
    assert config.default_backoff == 'x'
    assert config.default_loader == 'y'
    assert config.default_group == 'z'
    assert config.default_success_group == 'dsg'
    assert config.default_failure_group == 'dsf'

    assert config.pyproject_toml == {
        'arbkey': 123,
        'tool': {'pypyr': {
            'pipelines_subdir': 'arb4',
            'default_success_group': 'dsg'
        }}}

    assert config.config_loaded_paths == [Path('/cc2'),
                                          Path('/cc1'),
                                          Path('/cu'),
                                          Path('pyproject.toml'),
                                          Path('pypyr-config.yaml')]

    assert config.platform_paths == fake_pp_multiple_common

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc2'), encoding=None),
        call(Path('/cc1'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


@patch('pypyr.platform.get_platform_paths')
def test_config_init_all_files_found_scalars_and_dicts(mock_get_platform,
                                                       no_envs):
    """Heavy init merges all files with scalar and dict properties."""
    f1 = mock_open(read_data='pipelines_subdir: arb1\nvars:\n  a: b\n  f1: 1')
    f2 = mock_open(read_data='pipelines_subdir: arb2\nvars:\n  a: c\n  f2: 2')
    f3 = mock_open(read_data='pipelines_subdir: arb3\nvars:\n  a: d\n  f3: 3')
    f4 = mock_open(read_data=(
                   b'arbkey = 123\n'
                   b'[tool.pypyr]\n'
                   b'pipelines_subdir = "arb4"\n'
                   b'default_success_group = "dsg"\n'
                   b'[tool.pypyr.vars]\n'
                   b'a = "e"\n'
                   b'f4 = 4'))
    f5 = mock_open(
        read_data='pipelines_subdir: arb5\nvars:\n  a: f\n  f5: 5')

    mock_opens = [
        f1.return_value,
        f2.return_value,
        f3.return_value,
        f4.return_value,
        f5.return_value
    ]

    fake_pp_multiple_common = PlatformPaths(
        config_user=Path('/cu'),
        config_common=[Path('/cc1'), Path('/cc2')],
        data_dir_user=Path('/du'),
        data_dir_common=[Path('/dc')])

    mock_get_platform.return_value = fake_pp_multiple_common

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'arb5'
    assert config.default_backoff == 'fixed'
    assert config.default_loader == 'pypyr.loaders.file'
    assert config.default_group == 'steps'
    assert config.default_success_group == 'dsg'
    assert config.default_failure_group == 'on_failure'

    assert config.vars == {'a': 'f',
                           'f1': 1,
                           'f2': 2,
                           'f3': 3,
                           'f4': 4,
                           'f5': 5}

    assert config.shortcuts == {}

    assert config.pyproject_toml == {
        'arbkey': 123,
        'tool': {'pypyr': {
            'pipelines_subdir': 'arb4',
            'default_success_group': 'dsg',
            'vars': {
                'a': 'e',
                'f4': 4
            }
        }}}

    assert config.config_loaded_paths == [Path('/cc2'),
                                          Path('/cc1'),
                                          Path('/cu'),
                                          Path('pyproject.toml'),
                                          Path('pypyr-config.yaml')]

    assert config.platform_paths == fake_pp_multiple_common

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc2'), encoding=None),
        call(Path('/cc1'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


@patch('pypyr.platform.get_platform_paths')
def test_config_init_all_files_only_dicts(mock_get_platform,
                                          no_envs):
    """Heavy init merges all files with only dict properties."""
    f1 = mock_open(read_data='vars:\n  a: b\n  f1: 1')
    f2 = mock_open(read_data='vars:\n  a: c\n  f2: 2\nshortcuts:\n  s1: one')
    f3 = mock_open(read_data='vars:\n  a: d\n  f3: 3\nshortcuts:\n  s2: two')
    f4 = mock_open(read_data=(
                   b'arbkey = 123\n'
                   b'[tool.pypyr.vars]\n'
                   b'a = "e"\n'
                   b'f4 = 4\n'
                   b'[tool.pypyr.shortcuts]\n'
                   b's1 = "oneupdated"\n'))
    f5 = mock_open(
        read_data='vars:\n  a: f\n  f5: 5\nshortcuts:\n  s3: three')

    mock_opens = [
        f1.return_value,
        f2.return_value,
        f3.return_value,
        f4.return_value,
        f5.return_value
    ]

    fake_pp_multiple_common = PlatformPaths(
        config_user=Path('/cu'),
        config_common=[Path('/cc1'), Path('/cc2')],
        data_dir_user=Path('/du'),
        data_dir_common=[Path('/dc')])

    mock_get_platform.return_value = fake_pp_multiple_common

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_backoff == 'fixed'
    assert config.default_loader == 'pypyr.loaders.file'
    assert config.default_group == 'steps'
    assert config.default_failure_group == 'on_failure'

    assert config.vars == {'a': 'f',
                           'f1': 1,
                           'f2': 2,
                           'f3': 3,
                           'f4': 4,
                           'f5': 5}

    assert config.shortcuts == {'s1': 'oneupdated',
                                's2': 'two',
                                's3': 'three'}

    assert config.pyproject_toml == {
        'arbkey': 123,
        'tool': {'pypyr': {
            'vars': {
                'a': 'e',
                'f4': 4
            },
            'shortcuts': {
                's1': 'oneupdated'
            }
        }}}

    assert config.config_loaded_paths == [Path('/cc2'),
                                          Path('/cc1'),
                                          Path('/cu'),
                                          Path('pyproject.toml'),
                                          Path('pypyr-config.yaml')]

    assert config.platform_paths == fake_pp_multiple_common

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc2'), encoding=None),
        call(Path('/cc1'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


@patch('pypyr.platform.get_platform_paths', return_value=fake_platform_paths)
def test_config_init_property_invalid(mock_get_platform, no_envs):
    """Heavy init raises on invalid property."""
    f1 = mock_open(read_data='arb: varb1\narb2: varb2\ndefault_backoff: x')

    mock_opens = [
        f1.return_value
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        with pytest.raises(ConfigError) as err:
            config.init()

    assert mock_files.mock_calls == [call(Path('/cc'), encoding=None)]

    assert str(err.value) in ["Unexpected config props: {'arb2', 'arb'}",
                              "Unexpected config props: {'arb', 'arb2'}"]


@patch('pypyr.platform.get_platform_paths', return_value=fake_platform_paths)
def test_config_init_filename_set_by_env(mock_get_platform, monkeypatch):
    """Override config file name with $PYPYR_CONFIG_FILENAME."""
    monkeypatch.delenv('PYPYR_ENCODING', raising=False)
    monkeypatch.delenv('PYPYR_SKIP_INIT', raising=False)
    monkeypatch.delenv('PYPYR_CONFIG_GLOBAL', raising=False)
    monkeypatch.setenv('PYPYR_CONFIG_LOCAL', 'arb')
    mock_opens = [
        OSError,
        OSError(),
        OSError(),
        OSError
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_group == 'steps'
    assert config.pyproject_toml is None
    assert config.config_loaded_paths == []
    assert config.platform_paths == fake_platform_paths

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('arb'), encoding=None)]


def test_config_file_env_override(monkeypatch, no_envs):
    """Heavy init with $PYPYR_CONFIG_FILE override."""
    monkeypatch.setenv('PYPYR_CONFIG_GLOBAL', '/arb/path')

    f1 = mock_open(read_data='pipelines_subdir: arb')

    mock_opens = [
        f1.return_value,
        OSError(),
        OSError()
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    arb_path = Path('/arb/path')

    assert config.skip_init is False
    assert config.pipelines_subdir == 'arb'
    assert config.pyproject_toml is None
    assert config.config_loaded_paths == [arb_path]
    assert config.platform_paths == PlatformPaths(config_user=arb_path,
                                                  config_common=[arb_path],
                                                  data_dir_user=arb_path,
                                                  data_dir_common=[arb_path])

    assert mock_files.mock_calls == [
        call(Path('/arb/path'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


def test_config_file_env_override_merges_locals(monkeypatch, no_envs):
    """Heavy init with $PYPYR_CONFIG_FILE still merges ./ config files."""
    monkeypatch.setenv('PYPYR_CONFIG_GLOBAL', '/arb/path')

    f1 = mock_open(read_data='pipelines_subdir: arb')
    f2 = mock_open(read_data=(
        b'arbkey = 123\n'
                   b'[tool.pypyr]\n'
                   b'pipelines_subdir = "arb2"\n'
                   b'default_group = "stepsX"'))
    f3 = mock_open(read_data='pipelines_subdir: arb3\ndefault_backoff: xxx')

    mock_opens = [
        f1.return_value,
        f2.return_value,
        f3.return_value
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'arb3'
    assert config.default_group == 'stepsX'
    assert config.default_backoff == 'xxx'
    assert config.default_loader == 'pypyr.loaders.file'
    assert config.default_success_group == 'on_success'

    arb_path = Path('/arb/path')
    assert config.config_loaded_paths == [arb_path,
                                          Path('pyproject.toml'),
                                          Path('pypyr-config.yaml')]

    assert config.platform_paths == PlatformPaths(config_user=arb_path,
                                                  config_common=[arb_path],
                                                  data_dir_user=arb_path,
                                                  data_dir_common=[arb_path])
    assert config.pyproject_toml == {
        'arbkey': 123,
        'tool': {'pypyr': {
            'pipelines_subdir': 'arb2',
            'default_group': 'stepsX'
        }}}

    assert mock_files.mock_calls == [
        call(arb_path, encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


def test_config_file_env_override_not_found(monkeypatch, no_envs):
    """Heavy init with $PYPYR_CONFIG_FILE override raises on not found."""
    monkeypatch.setenv('PYPYR_CONFIG_GLOBAL', 'arb/path')

    config = Config()

    with patch('builtins.open', side_effect=OSError()) as f1:
        with pytest.raises(ConfigError) as err:
            config.init()

    path = Path('arb/path')
    assert str(err.value) == f'Could not open config file at {path}.'
    f1.assert_called_with(path, encoding=None)


def test_config_file_env_override_malformed(monkeypatch, no_envs):
    """Heavy init with $PYPYR_CONFIG_FILE override raises on not mapping."""
    monkeypatch.setenv('PYPYR_CONFIG_GLOBAL', 'arb/path')

    config = Config()

    with patch('builtins.open', mock_open(read_data='blah')) as f1:
        with pytest.raises(ConfigError) as err:
            config.init()

    path = Path('arb/path')
    assert str(err.value) == (
        f'Config file {path} should be a mapping (i.e a dict or table) at '
        'the top level.')
    f1.assert_called_with(path, encoding=None)

# endregion init (heavy)

# region pyproject.toml


@patch('pypyr.platform.get_platform_paths', return_value=fake_platform_paths)
def test_config_init_pyprojtoml_no_tool(mock_get_platform, no_envs):
    """Load pyproject.toml with no tool table."""
    f1 = mock_open(read_data=(
                   b'arbkey = 123\n'
                   b'[mytable]\n'
                   b'key1 = "arb4"\n'
                   b'default_success_group = "dsg"'))
    mock_opens = [
        OSError(),
        OSError(),
        f1.return_value,
        OSError()
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_success_group == 'on_success'

    assert config.pyproject_toml == {
        'arbkey': 123,
        'mytable': {
            'key1': 'arb4',
            'default_success_group': 'dsg'
        }}

    assert config.config_loaded_paths == []

    assert config.platform_paths == fake_platform_paths

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


@patch('pypyr.platform.get_platform_paths', return_value=fake_platform_paths)
def test_config_init_pyprojtoml_tool_no_pypyr(mock_get_platform, no_envs):
    """Load pyproject.toml with tool table but no pypyr.tool sub-table."""
    f1 = mock_open(read_data=(
                   b'arbkey = 123\n'
                   b'[tool.arbtool]\n'
                   b'key1 = "arb4"\n'
                   b'default_success_group = "dsg"'))
    mock_opens = [
        OSError(),
        OSError(),
        f1.return_value,
        OSError()
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_success_group == 'on_success'

    assert config.pyproject_toml == {
        'arbkey': 123,
        'tool': {'arbtool': {
            'key1': 'arb4',
            'default_success_group': 'dsg'
        }}}

    assert config.config_loaded_paths == []

    assert config.platform_paths == fake_platform_paths

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


@patch('pypyr.platform.get_platform_paths', return_value=fake_platform_paths)
def test_config_init_pyprojtoml_empty(mock_get_platform, no_envs):
    """Load pyproject.toml this is totally empty."""
    f1 = mock_open(read_data=(b''))
    mock_opens = [
        OSError(),
        OSError(),
        f1.return_value,
        OSError()
    ]

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_success_group == 'on_success'

    # tomli parses to None rather than {}
    assert config.pyproject_toml is None

    assert config.config_loaded_paths == []

    assert config.platform_paths == fake_platform_paths

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(Path('/cc'), encoding=None),
        call(Path('/cu'), encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]


def test_pyproject_toml_with_raise(no_envs):
    """Raise error option when pyproject.toml not found."""
    config = Config()
    with patch('builtins.open', side_effect=OSError) as mock_files:
        with pytest.raises(ConfigError) as err:
            config.load_pyproject_toml(Path('pyproject.toml'), True)

    assert str(err.value) == 'Could not open config file at pyproject.toml.'
    assert config.skip_init is False
    assert config.pipelines_subdir == 'pipelines'
    assert config.default_success_group == 'on_success'

    assert config.pyproject_toml is None

    assert config.config_loaded_paths == []

    mock_files.assert_called_once_with(Path('pyproject.toml'), 'rb')
# endregion pyproject.toml

# region __str__


def test_config_default_str(no_envs):
    """Config object default represents as nice friendly string."""
    config = Config()
    assert str(config) == f"""WRITEABLE PROPERTIES:

default_backoff: fixed
default_cmd_encoding:
default_encoding:
default_failure_group: on_failure
default_group: steps
default_loader: pypyr.loaders.file
default_success_group: on_success
json_ascii: false
json_indent: 2
log_config:
log_date_format: '%Y-%m-%d %H:%M:%S'
log_detail_format: '%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s'
log_notify_format: '%(message)s'
pipelines_subdir: pipelines
shortcuts: {{}}
vars: {{}}


COMPUTED PROPERTIES:

config_loaded_paths: []
cwd: {CWD}
is_macos: {is_macos}
is_posix: {is_posix}
is_windows: {is_windows}
platform: {current_platform}
platform_paths:
pyproject_toml:
skip_init: False
"""  # noqa: 501
    # the noqa is to ignore line length.


@patch('pypyr.platform.get_platform_paths')
def test_config_all_str(mock_get_platform, no_envs):
    """Config represents all properties as string after heavy init."""
    f1 = mock_open(read_data=(
                   b'arbkey = 123\n'
                   b'[tool.pypyr]\n'
                   b'pipelines_subdir = "arb4"\n'
                   b'default_success_group = "dsg"\n'
                   b'[tool.pypyr.vars]\n'
                   b'a = "e"\n'
                   b'f4 = 4'))
    f2 = mock_open(
        read_data=('pipelines_subdir: arb5\nvars: \n  a: f\n  f5: 5\n'
                   'shortcuts:\n  s1: one'))

    mock_opens = [
        OSError(),
        OSError(),
        f1.return_value,
        f2.return_value
    ]

    cu = Path('/cu')
    cc = Path('/cc')
    du = Path('/du')
    dc = Path('/dc')
    dc2 = Path('/dc2')

    fake_pp = PlatformPaths(config_user=cu,
                            config_common=[cc],
                            data_dir_user=du,
                            data_dir_common=[dc, dc2])

    mock_get_platform.return_value = fake_pp

    config = Config()

    with patch('builtins.open', side_effect=mock_opens) as mock_files:
        config.init()

    assert config.config_loaded_paths == [Path('pyproject.toml'),
                                          Path('pypyr-config.yaml')]

    assert config.platform_paths == fake_pp

    mock_get_platform.assert_called_once_with('pypyr', 'config.yaml')

    assert mock_files.mock_calls == [
        call(cc, encoding=None),
        call(cu, encoding=None),
        call(Path('pyproject.toml'), 'rb'),
        call(Path('pypyr-config.yaml'), encoding=None)]

    assert str(config) == f"""WRITEABLE PROPERTIES:

default_backoff: fixed
default_cmd_encoding:
default_encoding:
default_failure_group: on_failure
default_group: steps
default_loader: pypyr.loaders.file
default_success_group: dsg
json_ascii: false
json_indent: 2
log_config:
log_date_format: '%Y-%m-%d %H:%M:%S'
log_detail_format: '%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s'
log_notify_format: '%(message)s'
pipelines_subdir: arb5
shortcuts:
  s1: one
vars:
  a: f
  f4: 4
  f5: 5


COMPUTED PROPERTIES:

config_loaded_paths:
  - pyproject.toml
  - pypyr-config.yaml
cwd: {CWD}
is_macos: {is_macos}
is_posix: {is_posix}
is_windows: {is_windows}
platform: {current_platform}
platform_paths:
  config_user: {cu}
  config_common:
    - {cc}
  data_dir_user: {du}
  data_dir_common:
    - {dc}
    - {dc2}
pyproject_toml:
  arbkey: 123
  tool:
    pypyr:
      pipelines_subdir: arb4
      default_success_group: dsg
      vars:
        a: e
        f4: 4
skip_init: False
"""  # noqa: 501
    # the noqa is to ignore line length.
# endregion __str__
