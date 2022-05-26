"""Configuration settings.

Attributes:
    config: Use this global singleton from elsewere to access config values.
"""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Mapping
from io import StringIO
import os
from pathlib import Path
import sys
from typing import Any, Callable

import ruamel.yaml

import pypyr.errors
import pypyr.platform
import pypyr.toml
from pypyr.utils.types import cast_str_to_bool

CWD = Path.cwd()


class Config():
    """Configuration properties for pypyr.

    Look here for 'constant' values or configurable values.

    You probably shouldn't be instantiating this class directly yourself, use
    the global `config` attribute of this module instead, which contains a
    shared instance of this class - `from pypyr.config import config`.

    The standard constructor initializes the class with everything pypyr needs
    to run by default. Optionally, you can then also invoke init() on the
    instance to do heavier configuration setup that looks for the various
    config files on the filesystem, parses yaml+toml and reads the available
    values into the Config instance.

    NB: When adding attributes or properties to this class, remember to update
    Config.all_writable_props AND the custom __str__() overload also.

    Attributes:
        cwd: Path. The current working directory.
        json_indent: int. Indent for json output files.
        json_ascii: bool. If True escapes non-ascii chars.
        pipeline_subdir: str. 2nd pipeline look-up dir - subdir of cwd.
        log_config: dict. Logging config dict for logging.config.dictConfig.
        log_date_format: str. Format str for datetime in log output.
        log_notify_format: str. Format str for default log output.
        log_detail_format: str. Format str for detailed log output.
        default_backoff: str. Default retry back-off algorithm.
        default_cmd_encoding: str. Encoding to use on stdout/stderr with
            subprocess via pypyr.steps.cmd, pypyr.steps.cmds & shell.
        default_encoding: str. Encoding to use when working with files. None
            means to use the system defaults (utf-8, except for Windows.)
        default_loader: str. Default pipeline loader - 'pypyr.loaders.file'
        default_group: str. Step group name to run as entry-point - 'steps'.
        default_success_group: str. Name of step group to run on success -
                               'on_success'.
        default_failure_group: str. Name of step group to run on failure -
                               'on_failure'.
        shortcuts: dict. Pipeline run instructions with their inputs.
            Set by init().
        vars: dict. User provided variables to write into the pypyr context.
            Set by init().
        platform_paths: pypyr.platform.PlatformPaths: O/S specific paths to
            config files & data dirs. Set by init().
        pyproject_toml: dict. The pyproject.toml file as a dict in a full.
            Set by init().
        skip_init: bool. Default False. Skip the init() method if this set.
        config_loaded_paths: list[Path]. List of paths of the loaded config
            files, in the order loaded.
    """

    all_writable_props = {
        'json_ascii',
        'json_indent',
        'pipelines_subdir',
        # logging
        'log_config',
        'log_date_format',
        'log_notify_format',
        'log_detail_format',
        # defaults
        'default_backoff',
        'default_cmd_encoding',
        'default_encoding',
        'default_loader',
        'default_group',
        'default_success_group',
        'default_failure_group',
        # functional
        'shortcuts',
        'vars'}
    dict_props = {'shortcuts', 'vars'}
    scalar_props = all_writable_props - dict_props

    def __init__(self) -> None:
        """Initialize config with light-weight standard values."""
        # region writeable attributes

        # When adding an attr here, MUST add to Config.all_writable_props too.
        # Remember to amend custom __str__ overload when adding props/attrs.

        self.json_ascii = False
        self.json_indent = 2
        self.pipelines_subdir = 'pipelines'

        # logging
        self.log_config = None
        self.log_date_format = '%Y-%m-%d %H:%M:%S'
        self.log_notify_format = '%(message)s'
        self.log_detail_format = (
            '%(asctime)s %(levelname)s:%(name)s:%(funcName)s: %(message)s')

        # defaults
        self.default_backoff = 'fixed'
        # 'utf-8' is a magic string specially optimized in CPython
        self.default_cmd_encoding: str | None = os.getenv('PYPYR_CMD_ENCODING',
                                                          None)
        self.default_encoding: str | None = os.getenv('PYPYR_ENCODING', None)
        self.default_loader = 'pypyr.loaders.file'
        self.default_group = 'steps'
        self.default_success_group = 'on_success'
        self.default_failure_group = 'on_failure'

        # functional
        self.shortcuts: dict = {}
        self.vars: dict = {}

        # endregion writeable attributes

        # readonly properties set by default/light init
        current_platform = sys.platform
        self._platform: str = current_platform
        self._is_macos: bool = current_platform == 'darwin'
        self._is_windows: bool = current_platform == 'win32'
        self._is_posix: bool = not (self._is_macos or self._is_windows)

        # not writeable from config - readonly properties set by self.init()
        self._platform_paths: pypyr.platform.PlatformPaths | None = None
        self._pyproject_toml: dict | None = None
        self._skip_init = False
        self._config_loaded_paths: list[Path] = []

    @property
    def config_loaded_paths(self) -> list[Path] | None:
        """List of all the found config files loaded into runtime config.

        In the order that pypyr loaded the files.

        Set by init(). If init() didn't run, this is None.
        """
        return self._config_loaded_paths

    @property
    def cwd(self) -> Path:
        """Return the current working directory."""
        return CWD

    @property
    def is_macos(self) -> bool:
        """Is True if current platform is MacOS."""
        return self._is_macos

    @property
    def is_posix(self) -> bool:
        """Is True if current platform is POSIX."""
        return self._is_posix

    @property
    def is_windows(self) -> bool:
        """Is True if current platform is MacOS."""
        return self._is_windows

    @property
    def platform(self) -> str:
        """Platform (O/S) identifier."""
        return self._platform

    @property
    def platform_paths(self) -> pypyr.platform.PlatformPaths | None:
        """Platform specific paths & application directories.

        Set by init(). If init() didn't run, this is None. If no config files
        were found, this is None.
        """
        return self._platform_paths

    @property
    def pyproject_toml(self) -> dict | None:
        """Contents of ./pyproject_toml, if it exists.

        Set by init(). If init() didn't run, this is None. If init() ran but
        ./pyproject.toml didn't exist, also none.
        """
        return self._pyproject_toml

    @property
    def skip_init(self) -> bool:
        """Skip heavy init() - set by $PYPYR_SKIP_INIT."""
        return self._skip_init

    def init(self) -> None:
        """Heavy initialization to look-up config files on filesystem.

        Only call this if you want to load configuration settings from the
        config file look-up sequence. This is entirely optional - pypyr works
        with sensible defaults even when you don't want to call this.

        Order of precedence:
        1. /pypyr-config.yaml
        2. ./pyproject.toml
        3. Use $PYPYR_CONFIG_GLOBAL if available. If not, go to 4 & 5.
        4. $XDG_CONFIG_HOME - ~/.config/pypyr/config.yaml
        5. $XDG_CONFIG_DIRS/pypyr/config.yaml

        If $PYPYR_SKIP_INIT is 'true' or '1', this method returns without doing
        anything.
        """
        if cast_str_to_bool(os.getenv('PYPYR_SKIP_INIT', '0')):
            self._skip_init = True
            return

        # The final merge sticks, therefore go in reverse order 5 -> 1.
        env_config_path_str = os.getenv('PYPYR_CONFIG_GLOBAL', None)

        if env_config_path_str:
            # 3. Use $PYPYR_CONFIG_GLOBAL if available. If not, go to 4 & 5.
            env_config_path = Path(env_config_path_str)
            # Since user explicitly set this path, raise error if not exist.
            self.handle_path(env_config_path, raise_not_found=True)
            self._platform_paths = pypyr.platform.PlatformPaths(
                config_user=env_config_path,
                config_common=[env_config_path],
                data_dir_user=env_config_path,
                data_dir_common=[env_config_path])
        else:
            platform_paths = pypyr.platform.get_platform_paths('pypyr',
                                                               'config.yaml')

            self._platform_paths = platform_paths

            # 5. $XDG_CONFIG_DIRS/pypyr/config.yaml
            for path in reversed(platform_paths.config_common):
                # going in reverse order because the last update in the
                # sequence is the prevailing value.
                self.handle_path(path)

            # 4. $XDG_CONFIG_HOME - ~/.config/pypyr/config.yaml
            self.handle_path(platform_paths.config_user)

        # 2. ./pyproject.toml
        self.handle_path(Path('pyproject.toml'), self.load_pyproject_toml)

        # 1. /pypyr-config.yaml
        config_file_name = os.getenv('PYPYR_CONFIG_LOCAL',
                                     'pypyr-config.yaml')

        self.handle_path(Path(config_file_name))

    def handle_path(self,
                    path: Path,
                    handler: Callable | None = None,
                    raise_not_found: bool = False) -> None:
        """Load configuration file from path and merge into runtime config.

        handler signature is:
            handler(path: Path, raise_not_found: bool) -> Mapping

        If handler not specified, defaults to yaml loader.

        Args:
            path (Path): Path to file to load.
            handler (Callable): Callable that loads file and returns payload.
                                Defaults to yaml loader if not set.
            raise_not_found (bool): Raise error if file not found. Defaults
                                    to False.
        """
        payload = (handler(path, raise_not_found) if handler
                   else self.load_yaml(path, raise_not_found))

        if payload:
            if not isinstance(payload, Mapping):
                raise pypyr.errors.ConfigError(
                    f'Config file {path} should be a mapping (i.e a dict or '
                    'table) at the top level.')

            self.update(payload)
            self._config_loaded_paths.append(path)

    def update(self, input: Mapping) -> None:
        """Update self from input dict.

        Merges input dict into the current config instance (self).

        Args:
            input (Mapping): Merge this into the current instance.

        Returns: None
        """
        keys = input.keys()

        # 1. check all keys as expected
        difference = keys - Config.all_writable_props

        if difference:
            raise pypyr.errors.ConfigError(
                f'Unexpected config props: {difference}')

        # 2. update mapping keys
        dicts = keys & Config.dict_props
        for k in dicts:
            getattr(self, k).update(input[k])

        # 3. overwrite scalars
        scalars = keys & Config.scalar_props
        for k in scalars:
            setattr(self, k, input[k])

    def load_pyproject_toml(self, path: Path | str,
                            raise_error=False) -> Mapping | None:
        """Get pyproject toml config for pypyr.tool table.

        Args:
            path (Path): Path to file to load.
            raise_error (bool): Raise error if file not found. Defaults
                                to False.

        Returns:
            The [tool.pypyr] sub-table in the toml, if it exists.
        """
        try:
            toml = pypyr.toml.read_file(path)
        except OSError:
            if raise_error:
                raise pypyr.errors.ConfigError(
                    f'Could not open config file at {path}.') from OSError
            return None

        if toml:
            self._pyproject_toml = toml
            tool = toml.get('tool')
            if tool:
                return tool.get('pypyr')

        return None

    def load_yaml(self, path: Path | str, raise_error=False) -> Any:
        """Get config from yaml file.

        Args:
            path (Path): Path to file to load.
            raise_error (bool): Raise error if file not found. Defaults
                                to False.

        Returns:
            The yaml payload. Should be a Mapping, but could be any scalar or
            None.
        """
        parser = ruamel.yaml.YAML()
        try:
            # beg forgiveness later - mostly file WON'T be there.
            with open(path, encoding=self.default_encoding) as file:
                payload = parser.load(file)
        except OSError:
            if raise_error:
                raise pypyr.errors.ConfigError(
                    f'Could not open config file at {path}.') from OSError
            return None

        return payload

    def __str__(self) -> str:
        """Convert config to human friendly string."""
        # this might seem unnecessarily tedious - but neither pprint, nor dir()
        # or vars() give a consistent reliable listing of attributes + props
        # of interest.
        out = StringIO()
        yamler = ruamel.yaml.YAML()

        out.write('WRITEABLE PROPERTIES:\n\n')
        # instead of by hand creating str output, just dump yaml from dict
        # of all props
        writeable_props = {key: getattr(self, key)
                           for key in sorted(Config.all_writable_props)}

        yamler.dump(writeable_props, out)

        out.write('\n\nCOMPUTED PROPERTIES:\n\n')
        # the writeable props are all basic types, therefore the yaml dumper
        # knows what to do with them. The computed props use custom types,
        # which the yaml serializer can't handle without a custom serializer.
        # So either write a custom yaml serializer, or do it by hand. By hand
        # seemed less effort, comparatively.
        if self._config_loaded_paths:
            out.write('config_loaded_paths:\n')
            out.write(''.join(f'  - {k}\n' for k in self._config_loaded_paths))
        else:
            out.write('config_loaded_paths: []\n')

        out.write(f'cwd: {self.cwd}\n')

        out.write(f'is_macos: {self._is_macos}\n')
        out.write(f'is_posix: {self._is_posix}\n')
        out.write(f'is_windows: {self._is_windows}\n')
        out.write(f'platform: {self._platform}\n')

        if self._platform_paths:
            out.write(f'platform_paths:\n{self._platform_paths.to_str(2)}')
        else:
            out.write('platform_paths:\n')

        yamler.dump({'pyproject_toml': self._pyproject_toml}, out)

        out.write(f'skip_init: {self._skip_init}\n')
        return out.getvalue()


# global singleton of the config - use this to get your config values.
config = Config()
