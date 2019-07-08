from copy import deepcopy
from unittest.mock import MagicMock


class DeepCopyMagicMock(MagicMock):
    """Derive a new MagicMock doing a deepcopy of args to calls.

    MagicMocks store a reference to a mutable object - so on multiple calls to
    the mock the call history isn't maintained if the same obj mutates as an
    arg to those calls. https://bugs.python.org/issue33667

    It's probably not sensible to deepcopy all mock calls. So this little class
    is for patching the MagicMock class specifically, where it will do the
    deepcopy only where specifically patched.

    See here:
    https://docs.python.org/3/library/unittest.mock-examples.html#coping-with-mutable-arguments
    """

    def __call__(self, *args, **kwargs):
        """Mock call override does deepcopy."""
        return super(DeepCopyMagicMock, self).__call__(*deepcopy(args),
                                                       **deepcopy(kwargs))
