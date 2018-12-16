"""filewritejson.py unit tests."""
import pytest
import io
from unittest.mock import mock_open, patch
from pypyr.context import Context
from pypyr.errors import (
    ContextError,
    KeyInContextHasNoValueError,
    KeyNotInContextError)
import pypyr.steps.filewritejson as filewrite


def test_filewritejson_no_filewritejson_raises():
    """No input fileWriteJson raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteJson'] doesn't exist. "
        "It must exist for pypyr.steps.filewritejson.")


def test_filewritejson_none_filewritejson_raises():
    """None fileWriteJson raises."""
    context = Context({
        'k1': 'v1',
        'fileWriteJson': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteJson'] must have a value for "
        "pypyr.steps.filewritejson.")


def test_filewritejson_filewritejson_not_iterable_raises():
    """Not iterable fileWriteJson raises."""
    context = Context({
        'k1': 'v1',
        'fileWriteJson': 1})

    with pytest.raises(ContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteJson'] must be iterable "
        "and contain 'path' for pypyr.steps.filewritejson. argument of type "
        "'int' is not iterable")


def test_filewritejson_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fileWriteJson': {
            'path': None
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteJson']['path'] must have a value for "
        "pypyr.steps.filewritejson.")


def test_filewritejson_no_path_raises():
    """No path raises."""
    context = Context({
        'fileWriteJson': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == ("context['fileWriteJson']['path'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filewritejson.")


@patch('os.makedirs')
def test_filewritejson_pass_no_payload(mock_makedirs):
    """Success case writes all context out when no payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteJson': {
            'path': '/arb/blah'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewritejson.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteJson'] == {'path': '/arb/blah'}

        mock_makedirs.assert_called_once_with('/arb', exist_ok=True)
        mock_output.assert_called_once_with('/arb/blah', 'w')
        # json well formed & new lines and indents are where they should be
        assert out_text.getvalue() == ('{\n'
                                       '    "k1": "v1",\n'
                                       '    "fileWriteJson": {\n'
                                       '        "path": "/arb/blah"\n'
                                       '    }\n'
                                       '}')


@patch('os.makedirs')
def test_filewritejson_pass_with_payload(mock_makedirs):
    """Success case writes only specific context payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteJson': {
            'path': '/arb/blah',
            'payload': [
                'first',
                'second',
                {'a': 'b', 'c': 123.45, 'd': [0, 1, 2]},
                12,
                True
            ]
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewritejson.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteJson']['payload'] == [
            'first',
            'second',
            {'a': 'b', 'c': 123.45,
             'd': [0, 1, 2]},
            12,
            True
        ]
        assert context['fileWriteJson'] == {'path': '/arb/blah',
                                            'payload': [
                                                'first',
                                                'second',
                                                {'a': 'b',
                                                 'c': 123.45,
                                                 'd': [0, 1, 2]},
                                                12,
                                                True
                                            ]}

        mock_makedirs.assert_called_once_with('/arb', exist_ok=True)
        mock_output.assert_called_once_with('/arb/blah', 'w')
        # json well formed & new lines + indents are where they should be
        assert out_text.getvalue() == ('[\n'
                                       '    "first",\n'
                                       '    "second",\n'
                                       '    {\n'
                                       '        "a": "b",\n'
                                       '        "c": 123.45,\n'
                                       '        "d": [\n'
                                       '            0,\n'
                                       '            1,\n'
                                       '            2\n'
                                       '        ]\n'
                                       '    },\n'
                                       '    12,\n'
                                       '    true\n'
                                       ']')


@patch('os.makedirs')
def test_filewritejson_pass_no_payload_substitutions(mock_makedirs):
    """Success case writes all context out with substitutions."""
    context = Context({
        'k1': 'v1',
        'pathkey': '/arb/path',
        'parent': [0, 1, {'child': '{k1}'}],
        'nested': '{parent[2][child]}',
        'fileWriteJson': {
            'path': '{pathkey}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewritejson.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 5, "context should have 5 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteJson'] == {'path': '{pathkey}'}

        mock_makedirs.assert_called_once_with('/arb', exist_ok=True)
        mock_output.assert_called_once_with('/arb/path', 'w')
        # json well formed & new lines + indents are where they should be
        assert out_text.getvalue() == ('{\n'
                                       '    "k1": "v1",\n'
                                       '    "pathkey": "/arb/path",\n'
                                       '    "parent": [\n'
                                       '        0,\n'
                                       '        1,\n'
                                       '        {\n'
                                       '            "child": "v1"\n'
                                       '        }\n'
                                       '    ],\n'
                                       '    "nested": "v1",\n'
                                       '    "fileWriteJson": {\n'
                                       '        "path": "/arb/path"\n'
                                       '    }\n'
                                       '}')


@patch('os.makedirs')
def test_filewritejson_pass_with_payload_subsitutions(mock_makedirs):
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
        'fileWriteJson': {
            'path': '{pathkey}',
            'payload': '{parent[2]}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewritejson.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 6, "context should have 6 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteJson'] == {'path': '{pathkey}',
                                            'payload': '{parent[2]}'}
        assert context['parent'] == [0,
                                     1,
                                     {'child': ['{k1}',
                                                '{intkey}',
                                                ['a', 'b', 'c']
                                                ]
                                      }
                                     ]

        mock_makedirs.assert_called_once_with('/arb', exist_ok=True)
        mock_output.assert_called_once_with('/arb/path', 'w')
        # json well formed & new lines + indents are where they should be
        assert out_text.getvalue() == (
            '{\n'
            '    "child": [\n'
            '        "v1",\n'
            '        3,\n'
            '        [\n'
            '            "a",\n'
            '            "b",\n'
            '            "c"\n'
            '        ]\n'
            '    ]\n'
            '}')


@patch('os.makedirs')
def test_filewritejson_pass_with_empty_payload(mock_makedirs):
    """Empty payload write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWriteJson': {
            'path': '/arb/blah',
            'payload': ''
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewritejson.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteJson']['path'] == '/arb/blah'
        assert context['fileWriteJson']['payload'] == ''

        mock_makedirs.assert_called_once_with('/arb', exist_ok=True)
        mock_output.assert_called_once_with('/arb/blah', 'w')
        # json well formed & new lines + indents are where they should be
        assert out_text.getvalue() == '""'


@patch('os.makedirs')
def test_filewritejson_pass_with_none_payload(mock_makedirs):
    """None payload write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWriteJson': {
            'path': '/arb/blah',
            'payload': None
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewritejson.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteJson']['path'] == '/arb/blah'
        assert context['fileWriteJson']['payload'] is None

        mock_makedirs.assert_called_once_with('/arb', exist_ok=True)
        mock_output.assert_called_once_with('/arb/blah', 'w')
        # json well formed & new lines + indents are where they should be
        assert out_text.getvalue() == "null"
