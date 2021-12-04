"""tomlfile.py unit tests."""
from unittest.mock import mock_open, patch

import pytest

import pypyr.parser.tomlfile as toml_file


def test_toml_parser_file_open_fails_on_arbitrary_string():
    """Non path-y input string should fail."""
    with pytest.raises(FileNotFoundError):
        toml_file.get_parsed_context('value 1,value 2, value3')


def test_toml__parser_file_open_returns_none_on_empty_string():
    """Non path-y input string should fail."""
    assert toml_file.get_parsed_context('') is None


def test_toml_parser_file_open_returns_none_on_none():
    """Non path-y input string should fail."""
    assert toml_file.get_parsed_context(None) is None


def test_toml_parser_pass():
    """Path should pass to toml parser and return parsed toml as dict."""
    in_bytes = b'[table]\nkey= "value"'

    with patch('pypyr.toml.open',
               mock_open(read_data=in_bytes)) as mocked_open:
        out = toml_file.get_parsed_context(['./myfile.toml'])

    mocked_open.assert_called_once_with('./myfile.toml', 'rb')

    assert out == {'table': {'key': 'value'}}


def test_toml_parser_spaces():
    """Unescaped path with spaces pass."""
    in_bytes = b'key= "value"'

    with patch('pypyr.toml.open',
               mock_open(read_data=in_bytes)) as mocked_open:
        out = toml_file.get_parsed_context(['/mydir/sub/one',
                                            'two/my',
                                            'file.toml'])

    mocked_open.assert_called_once_with('/mydir/sub/one two/my file.toml',
                                        'rb')

    assert out == {'key': 'value'}
