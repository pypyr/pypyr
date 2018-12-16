"""Version information."""

import platform

__version__ = '2.0.0'


def get_version():
    return (f'pypyr {__version__} '
            f'python {platform.python_version()}')
