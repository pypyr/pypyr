"""filewriteyaml.py unit tests."""
import io
from unittest.mock import mock_open, patch

import pytest

from pypyr.context import Context
from pypyr.dsl import Jsonify
from pypyr.errors import (
    ContextError,
    KeyInContextHasNoValueError,
    KeyNotInContextError)
import pypyr.steps.filewriteyaml as filewrite


def test_filewriteyaml_no_filewriteyaml_raises():
    """No input fileWriteYaml raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteYaml'] doesn't exist. "
        "It must exist for pypyr.steps.filewriteyaml.")


def test_filewriteyaml_none_filewriteyaml_raises():
    """None fileWriteYaml raises."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteYaml'] must have a value for "
        "pypyr.steps.filewriteyaml.")


def test_filewriteyaml_filewriteyaml_not_iterable_raises():
    """Not iterable fileWriteYaml raises."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': 1})

    with pytest.raises(ContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteYaml'] must exist, be iterable "
        "and contain 'path' for pypyr.steps.filewriteyaml. argument of type "
        "'int' is not iterable")


def test_filewriteyaml_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fileWriteYaml': {
            'path': None
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWriteYaml']['path'] must have a value for "
        "pypyr.steps.filewriteyaml.")


def test_filewriteyaml_no_path_raises():
    """No path raises."""
    context = Context({
        'fileWriteYaml': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == ("context['fileWriteYaml']['path'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filewriteyaml.")


@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_no_payload(mock_path):
    """Success case writes all context out when no payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': {
            'path': '/arb/blah'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml'] == {'path': '/arb/blah'}

        mock_path.assert_called_once_with('/arb/blah')
        mocked_path = mock_path.return_value
        mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                         exist_ok=True)
        mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

        # yaml well formed & new lines and indents are where they should be
        assert out_text.getvalue() == ('k1: v1\n'
                                       'fileWriteYaml:\n'
                                       '  path: /arb/blah\n')


@patch('pypyr.config.config.default_encoding', new='utf-8')
@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_with_payload(mock_path):
    """Success case writes only specific context payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': {
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
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml']['payload'] == [
            'first',
            'second',
            {'a': 'b', 'c': 123.45,
             'd': [0, 1, 2]},
            12,
            True
        ]
        assert context['fileWriteYaml'] == {'path': '/arb/blah',
                                            'payload': [
                                                'first',
                                                'second',
                                                {'a': 'b',
                                                 'c': 123.45,
                                                 'd': [0, 1, 2]},
                                                12,
                                                True
                                            ]}

        mock_path.assert_called_once_with('/arb/blah')
        mocked_path = mock_path.return_value
        mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                         exist_ok=True)
        mock_output.assert_called_once_with(mocked_path, 'w', encoding='utf-8')

        # yaml well formed & new lines + indents are where they should be
        assert out_text.getvalue() == ('  - first\n'
                                       '  - second\n'
                                       '  - a: b\n'
                                       '    c: 123.45\n'
                                       '    d:\n'
                                       '      - 0\n'
                                       '      - 1\n'
                                       '      - 2\n'
                                       '  - 12\n'
                                       '  - true\n')


@patch('pypyr.config.config.default_encoding', new='utf-8')
@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_with_payload_encoding_set(mock_path):
    """Success case writes only specific context payload."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': {
            'path': '/arb/blah',
            'payload': [
                'first',
                'second',
                {'a': 'b', 'c': 123.45, 'd': [0, 1, 2]},
                12,
                True
            ],
            'encoding': 'utf-16'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml']['payload'] == [
            'first',
            'second',
            {'a': 'b', 'c': 123.45,
             'd': [0, 1, 2]},
            12,
            True
        ]
        assert context['fileWriteYaml'] == {'path': '/arb/blah',
                                            'payload': [
                                                'first',
                                                'second',
                                                {'a': 'b',
                                                 'c': 123.45,
                                                 'd': [0, 1, 2]},
                                                12,
                                                True
                                            ],
                                            'encoding': 'utf-16'}

        mock_path.assert_called_once_with('/arb/blah')
        mocked_path = mock_path.return_value
        mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                         exist_ok=True)
        mock_output.assert_called_once_with(
            mocked_path, 'w', encoding='utf-16')

        # yaml well formed & new lines + indents are where they should be
        assert out_text.getvalue() == ('  - first\n'
                                       '  - second\n'
                                       '  - a: b\n'
                                       '    c: 123.45\n'
                                       '    d:\n'
                                       '      - 0\n'
                                       '      - 1\n'
                                       '      - 2\n'
                                       '  - 12\n'
                                       '  - true\n')


@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_no_payload_substitutions(mock_path):
    """Success case writes all context out with substitutions."""
    context = Context({
        'k1': 'v1',
        'pathkey': '/arb/path',
        'parent': [0, 1, {'child': '{k1}'}],
        'nested': '{parent[2][child]}',
        'jsonify': Jsonify({'arb': 123}),
        'fileWriteYaml': {
            'path': '{pathkey}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 6, "context should have 6 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml'] == {'path': '{pathkey}'}

        mock_path.assert_called_once_with('/arb/path')
        mocked_path = mock_path.return_value
        mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                         exist_ok=True)
        mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

        # yaml well formed & new lines + indents are where they should be
        assert out_text.getvalue() == ('k1: v1\n'
                                       'pathkey: /arb/path\n'
                                       'parent:\n'
                                       '  - 0\n'
                                       '  - 1\n'
                                       '  - child: v1\n'
                                       'nested: v1\n'
                                       'jsonify: \'{"arb": 123}\'\n'
                                       'fileWriteYaml:\n'
                                       '  path: /arb/path\n')


@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_with_payload_substitutions(mock_path):
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
        'fileWriteYaml': {
            'path': '{pathkey}',
            'payload': '{parent[2]}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 6, "context should have 6 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml'] == {'path': '{pathkey}',
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
        mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)
        # yaml well formed & new lines + indents are where they should be
        assert out_text.getvalue() == ('child:\n'
                                       '  - v1\n'
                                       '  - 3\n'
                                       '  -   - a\n'
                                       '      - b\n'
                                       '      - c\n')


@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_with_empty_payload(mock_path):
    """Empty payload write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': {
            'path': '/arb/blah',
            'payload': ''
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml']['path'] == '/arb/blah'
        assert context['fileWriteYaml']['payload'] == ''

        mock_path.assert_called_once_with('/arb/blah')
        mocked_path = mock_path.return_value
        mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                         exist_ok=True)
        mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)
        # yaml well formed & new lines + indents are where they should be
        assert out_text.getvalue() == "''\n"


@patch('pypyr.steps.filewriteyaml.Path')
def test_filewriteyaml_pass_with_none_payload(mock_path):
    """None payload write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWriteYaml': {
            'path': '/arb/blah',
            'payload': None
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewriteyaml.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        assert context, "context shouldn't be None"
        assert len(context) == 2, "context should have 2 items"
        assert context['k1'] == 'v1'
        assert context['fileWriteYaml']['path'] == '/arb/blah'
        assert context['fileWriteYaml']['payload'] is None

        mock_path.assert_called_once_with('/arb/blah')
        mocked_path = mock_path.return_value
        mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                         exist_ok=True)
        mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)
        # yaml well formed & new lines + indents are where they should be
        assert out_text.getvalue() == "null\n...\n"
