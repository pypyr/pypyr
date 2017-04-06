"""Version information."""

import platform

__version__ = '0.0.10'


def get_version():
    return f'%(prog)s {__version__} python {platform.python_version()}'
