"""errors.py unit tests."""
from pypyr.errors import Error as PypyrError
from pypyr.errors import PlugInError
import pytest


def test_base_error_raises():
    """Pypyr root Error raises with correct message."""
    with pytest.raises(PypyrError) as err_info:
        raise PypyrError("this is error text right here")

    assert repr(err_info.value) == ("Error('this is error text "
                                    "right here',)")


def test_plugin_error_raises():
    """Pypyr plugin error raises with correct message."""
    with pytest.raises(PlugInError) as err_info:
        raise PlugInError("this is error text right here")

    # confirm subclassed from pypyr root error
    assert isinstance(PlugInError(), PypyrError)
    assert repr(err_info.value) == ("PlugInError('this is error "
                                    "text right here',)")
