"""version.py unit tests."""
import pypyr.version
import platform


def test_get_version():
    """Test version as expected."""
    actual = pypyr.version.get_version()
    expected = (f'pypyr {pypyr.version.__version__} '
                f'python {platform.python_version()}')
    assert actual == expected, "version not returning correctly"
