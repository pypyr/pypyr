"""__main__.py unit tests."""
import pypyr.__main__
from unittest.mock import patch


def test_main_calls_main():
    """The python -m entry point should call pypyr.cli.main()."""
    with patch('pypyr.cli.main') as mock_cli_main:
        pypyr.__main__.main()

    mock_cli_main.assert_called_once()
