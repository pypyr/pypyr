"""Version information."""

import platform

__version__ = '3.2.0'


def get_version():
    return (f'pypyr {__version__} '
            f'python {platform.python_version()}')
