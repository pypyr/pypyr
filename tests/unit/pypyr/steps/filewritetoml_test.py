"""filewritetoml.py unit tests."""
import io
from unittest.mock import mock_open, patch

import pytest

from pypyr.context import Context
from pypyr.errors import (
    ContextError,
    KeyInContextHasNoValueError,
    KeyNotInContextError)
import pypyr.steps.filewritetoml as filewrite


def test_filewritetoml_no_filewritetoml_raises():
    """No input fileWriteToml raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteToml'] doesn't exist. "
        "It must exist for pypyr.steps.filewritetoml.")


def test_filewritetoml_none_filewritetoml_raises():
    """None fileWriteToml raises."""
    context = Context({
        'k1': 'v1',
        'fileWriteToml': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteToml'] must have a value for "
        "pypyr.steps.filewritetoml.")


def test_filewritetoml_filewritetoml_not_iterable_raises():
    """Not iterable fileWriteToml raises."""
    context = Context({
        'k1': 'v1',
        'fileWriteToml': 1})

    with pytest.raises(ContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteToml'] must exist, be iterable "
        "and contain 'path' for pypyr.steps.filewritetoml. argument of type "
        "'int' is not iterable")


def test_filewritetoml_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fileWriteToml': {
            'path': None
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteToml']['path'] must have a value for "
        "pypyr.steps.filewritetoml.")


def test_filewritetoml_no_path_raises():
    """No path raises."""
    context = Context({
        'fileWriteToml': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == ("context['fileWriteToml']['path'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filewritetoml.")


@patch('pypyr.steps.filewritetoml.Path')
def test_filewritetoml_pass_no_payload(mock_path):
    """Success case writes all context out when no payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteToml': {
            'path': '/arb/blah'
        }})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.toml.open', mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        output = out_bytes.getvalue().decode()

    mocked_path = mock_path.return_value
    mock_path.assert_called_once_with('/arb/blah')
    mock_output.assert_called_once_with(mocked_path, 'wb')
    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'v1'
    assert context['fileWriteToml'] == {'path': '/arb/blah'}

    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)

    # toml well formed & new lines and indents are where they should be
    assert output == 'k1 = "v1"\n\n[fileWriteToml]\npath = "/arb/blah"\n'


@patch('pypyr.steps.filewritetoml.Path')
def test_filewritetoml_pass_with_payload(mock_path):
    """Success case writes only specific context payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteToml': {
            'path': '/arb/blah',
            'payload': {
                'one': 'v1',
                'two': True,
                'three': {'a': 'b', 'c': 123.45,
                          'd': [0, 1, 2]},
                'four': 12,
                'five': True
            }}})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.toml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        output = out_bytes.getvalue().decode()

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'v1'

    assert context['fileWriteToml'] == {'path': '/arb/blah',
                                        'payload': {
                                            'one': 'v1',
                                            'two': True,
                                            'three': {'a': 'b', 'c': 123.45,
                                                      'd': [0, 1, 2]},
                                            'four': 12,
                                            'five': True
                                        }}

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'wb')

    # toml well formed & new lines + indents are where they should be
    assert output == ('one = "v1"\n'
                      'two = true\n'
                      'four = 12\n'
                      'five = true\n'
                      '\n'
                      '[three]\n'
                      'a = "b"\n'
                      'c = 123.45\n'
                      'd = [\n'
                      '    0,\n'
                      '    1,\n'
                      '    2,\n'
                      ']\n')


@patch('pypyr.steps.filewritetoml.Path')
def test_filewritetoml_pass_no_payload_substitutions(mock_path):
    """Success case writes all context out with substitutions."""
    context = Context({
        'k1': 'v1',
        'pathkey': '/arb/path',
        'parent': [0, 1, {'child': '{k1}'}],
        'nested': '{parent[2][child]}',
        'fileWriteToml': {
            'path': '{pathkey}'
        }})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.toml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        output = out_bytes.getvalue().decode()

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['k1'] == 'v1'
    assert context['fileWriteToml'] == {'path': '{pathkey}'}

    mock_path.assert_called_once_with('/arb/path')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'wb')

    # toml well formed & new lines + indents are where they should be
    assert output == ('k1 = "v1"\n'
                      'pathkey = "/arb/path"\n'
                      'parent = [\n'
                      '    0,\n'
                      '    1,\n'
                      '    { child = "v1" },\n'
                      ']\n'
                      'nested = "v1"\n'
                      '\n'
                      '[fileWriteToml]\n'
                      'path = "/arb/path"\n')


@patch('pypyr.steps.filewritetoml.Path')
def test_filewritetoml_pass_with_payload_substitutions(mock_path):
    """Success case writes only specified context with substitutions."""
    context = Context({
        'k1': 'v1',
        'intkey': 3,
        'pathkey': '/arb/path',
        'parent': [0,
                   1,
                   {'child': ['{k1}',
                              '{intkey}',
                              ['a', 'b', 'c']
                              ]}],
        'nested': '{parent[2][child]}',
        'fileWriteToml': {
            'path': '{pathkey}',
            'payload': '{parent[2]}'
        }})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.toml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        output = out_bytes.getvalue().decode()

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileWriteToml'] == {'path': '{pathkey}',
                                        'payload': '{parent[2]}'}
    assert context['parent'] == [0,
                                 1,
                                 {'child': ['{k1}',
                                            '{intkey}',
                                            ['a', 'b', 'c']
                                            ]
                                  }
                                 ]

    mock_path.assert_called_once_with('/arb/path')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'wb')

    # toml well formed & new lines + indents are where they should be
    assert output == ('child = [\n'
                      '    "v1",\n'
                      '    3,\n'
                      '    [\n'
                      '        "a",\n'
                      '        "b",\n'
                      '        "c",\n'
                      '    ],\n'
                      ']\n')


def test_filewritetoml_fail_with_empty_payload():
    """Empty payload does not write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWriteToml': {
            'path': '/arb/blah',
            'payload': ''
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err:
        filewrite.run_step(context)

    assert str(err.value) == (
        'payload must have a value to write to output TOML document.')


def test_filewritetoml_fail_with_none_payload():
    """None payload does not write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWriteToml': {
            'path': '/arb/blah',
            'payload': None
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err:
        filewrite.run_step(context)

    assert str(err.value) == (
        'payload must have a value to write to output TOML document.')
