"""Platform specific handling. For example, O/S specific directories.

Although it is not a direct copy and it's been substantially adjusted to fit
with pypyr's opinionated implementation, this module still owes a LOT of
inspiration to the PlatformDirs library, licensed under the MIT license.

https://github.com/platformdirs/platformdirs

This is the PlatformDirs license notice: This is the MIT license

Copyright (c) 2010 ActiveState Software Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""  # noqa: E501
# the noqa is for line length.
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from abc import ABC, abstractmethod
import os
from pathlib import Path
import re
import sys
from typing import Type, NamedTuple
# NB: This module pypyr.platform should NOT import anything from anywhere in
# pypyr, to prevent circular imports. Reason is pypyr.config imports this, and
# pypyr.config is used all over as a fundamental ground-level dependency.


class PlatformPaths(NamedTuple):
    """Platform specific paths for config files and data directories.

    The reason for declaring the NamedTuple like this is
    a) to make type information available
    b) allow the custom __str__ override.
    """

    config_user: Path
    config_common: list[Path]
    data_dir_user: Path
    data_dir_common: list[Path]

    def __str__(self) -> str:
        """Represent as friendly string with 0 offset."""
        return self.to_str()

    def to_str(self, offset: int = 0) -> str:
        """Represent class as human friendly string.

        Args:
            offset: Pad on left with this many spaces.

        Return:
            String representation of object.
        """
        offset_str = ' ' * offset
        return (f'{offset_str}config_user: {self.config_user}\n'
                + f'{offset_str}config_common:\n'
                + ''.join(f'{offset_str}  - {p}\n' for p in self.config_common)
                + f'{offset_str}data_dir_user: {self.data_dir_user}\n'
                + f'{offset_str}data_dir_common:\n'
                + ''.join(
                    f'{offset_str}  - {p}\n' for p in self.data_dir_common)
                )


class BaseDirFinder(ABC):
    """All platform specific directory finders derive from this."""

    def __init__(self, app_name: str, config_file_name: str) -> None:
        """Initialize app_name and config_file_name."""
        self.app_name = app_name  # pypyr
        self.config_file_name = config_file_name  # config.yaml

    def get_platform_paths(self) -> PlatformPaths:
        """Construct a PlatformPaths instance specific to this platform."""
        return PlatformPaths(config_user=self.get_config_user(),
                             config_common=self.get_config_common(),
                             data_dir_user=self.get_data_user(),
                             data_dir_common=self.get_data_common())

    @abstractmethod
    def get_config_user(self) -> Path:
        """Get path to user config file."""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def get_config_common(self) -> list[Path]:
        """Get paths to shared system-level config files."""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def get_data_user(self) -> Path:
        """Get user data directory for this platform."""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def get_data_common(self) -> list[Path]:
        """Get shared system-level data directory for this platform."""
        raise NotImplementedError()  # pragma: no cover


class Xdg(BaseDirFinder):
    """Find directories based on the XDG Base Dir specification."""

    def __init__(self, app_name: str, config_file_name: str):
        """Initialize defaults."""
        super().__init__(app_name, config_file_name)

        self.common_config_base_dir_default = '/etc/xdg'
        self.common_data_base_dir_default = (
            f'/usr/local/share{os.pathsep}/usr/share')

    def get_config_user(self) -> Path:
        """Get $XDG_CONFIG_HOME/config_file_name.

        Default dir is ~/.config/app_name/config_file_name.
        """
        path = os.getenv('XDG_CONFIG_HOME', '')
        if not path.strip():
            path = os.path.expanduser('~/.config')

        return self.get_pypyr_config_file_appended(path)

    def get_config_common(self) -> list[Path]:
        """Get list of dirs at $XDG_CONFIG_DIRS.

        app_name/config_file_name appended to each dir.
        """
        path = os.getenv('XDG_CONFIG_DIRS', '')
        if not path.strip():
            path = self.common_config_base_dir_default

        return [self.get_pypyr_config_file_appended(p)
                for p in path.split(os.pathsep) if p.strip()]

    def get_data_user(self) -> Path:
        """Get $XDG_DATA_HOME. Default is ~/.local/share/app_name."""
        path = os.getenv('XDG_DATA_HOME', '')
        if not path.strip():
            path = os.path.expanduser('~/.local/share')

        return Path(path, self.app_name)

    def get_data_common(self) -> list[Path]:
        """Get $XDG_DATA_DIRS.

        Default is
            /usr/local/share/app_name
            /usr/share/app_name
        """
        path = os.getenv('XDG_DATA_DIRS', '')
        if not path.strip():
            path = self.common_data_base_dir_default

        app_name = self.app_name
        return [Path(p, app_name) for p in path.split(os.pathsep) if p.strip()]

    def get_pypyr_config_file_appended(self, base_path: str) -> Path:
        """Append app_name and config_file_name to base_path."""
        return Path(base_path, self.app_name, self.config_file_name)


class MacOs(Xdg):
    """Find platform directories for MacOs.

    Largely follows XDG spec, except for the common dirs.
    """

    def __init__(self, app_name: str, config_file_name: str):
        """Initialize MacOs platform directories."""
        super().__init__(app_name, config_file_name)
        self.common_config_base_dir_default = '/Library/Application Support'
        self.common_data_base_dir_default = '/Library/Application Support'


class Windows(Xdg):
    """Find platform directories for Windows.

    Largely follows XDG spec, except for the common (i.e all user) dirs.
    """

    def __init__(self, app_name: str, config_file_name: str):
        """Initialize Windows directory finder."""
        super().__init__(app_name, config_file_name)
        common_appdata = os.getenv('ALLUSERSPROFILE', 'C:/ProgramData')

        self.common_config_base_dir_default = common_appdata
        self.common_data_base_dir_default = common_appdata


class Android(BaseDirFinder):
    """Find platform directories for Android."""

    def __init__(self, app_name, config_file_name):
        """Initialize Android directory finder."""
        super().__init__(app_name, config_file_name)
        android_dir = Path(Android._get_android_dir())
        self._config_path = android_dir.joinpath('shared_prefs',
                                                 self.app_name,
                                                 self.config_file_name)

        self._data_dir = android_dir.joinpath('files', app_name)

    def get_config_user(self) -> Path:
        """Return config directory for the user.

        e.g. ``/data/user/<userid>/<packagename>/shared_prefs/<AppName>``
        """
        return self._config_path

    def get_config_common(self) -> list[Path]:
        """Get common config path. Same as get_config_user."""
        return [self._config_path]

    def get_data_user(self) -> Path:
        """Return data directory for the user.

        e.g. ``/data/user/<userid>/<packagename>/files/<AppName>``
        """
        return self._data_dir

    def get_data_common(self) -> list[Path]:
        """Get common data dir. Same as get_data_user."""
        return [self._data_dir]

    @staticmethod
    def _get_android_dir() -> str:
        """Return the base folder for the Android OS.

        This method is wholly borrowed from PlatformDirs, with thanks!
        """
        try:
            # First try to get path to android app via pyjnius
            from jnius import autoclass  # type: ignore # noqa: SC200

            Context = autoclass('android.content.Context')  # noqa: SC200
            s: str = Context.getFilesDir().getParentFile().getAbsolutePath()
        except Exception:
            # if fails find an android folder looking path on the sys.path
            pattern = re.compile(r"/data/(data|user/\d+)/(.+)/files")
            for path in sys.path:
                if pattern.match(path):
                    s = path.split('/files')[0]
                    break
            else:
                raise OSError("Cannot find path to android app folder")
        return s


def get_platform_paths(app_name: str, config_file_name: str) -> PlatformPaths:
    """Calculate platform specific paths for this O/S.

    Args:
        app_name: Name of application. This forms part of the directory name.
        config_file_name: The name of the config file to append to config dirs.

    Returns:
        An instance of the PlatformPaths tuple, containing the paths relevant
        for this O/S.
    """
    platform_type = get_platform_dir_finder()
    dir_finder = platform_type(app_name, config_file_name)

    return dir_finder.get_platform_paths()


def get_platform_dir_finder() -> Type[BaseDirFinder]:
    """Return the BaseDirFinder specific to current O/S platform.

    The logic is pretty much to treat everything that is neither Windows, MacOs
    nor Android as POSIX. Android is checked via ANDROID_* env variables.

    This is a factory function. If you're trying to find platform specific
    paths, you should probably use get_platform_paths instead.

    Returns:
        Derived instance of BaseDirFinder appropriate to the current O/S.
    """
    current_platform = sys.platform
    platform_type: Type[BaseDirFinder]
    if (os.getenv('ANDROID_DATA') == '/data'
            and os.getenv('ANDROID_ROOT') == '/system'):
        platform_type = Android
    elif current_platform == 'win32':
        platform_type = Windows
    elif current_platform == 'darwin':
        platform_type = MacOs
    else:
        platform_type = Xdg

    return platform_type
