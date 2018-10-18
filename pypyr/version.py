"""Version information."""

import platform

__version__ = '1.1.1'


def get_version():
    return (f'pypyr {__version__} '
            f'python {platform.python_version()}')
