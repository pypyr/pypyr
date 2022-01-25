"""fileWrite.py unit tests."""
import io
from unittest.mock import mock_open, patch

import pytest

from pypyr.context import Context
from pypyr.errors import (
    ContextError,
    KeyInContextHasNoValueError,
    KeyNotInContextError)
import pypyr.steps.filewrite as filewrite

# region validation


def test_filewrite_no_input_raises():
    """No input fileWrite raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWrite'] doesn't exist. "
        "It must exist for pypyr.steps.filewrite.")


def test_filewrite_none_filewrite_raises():
    """None fileWrite raises."""
    context = Context({
        'k1': 'v1',
        'fileWrite': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWrite'] must have a value for "
        "pypyr.steps.filewrite.")


def test_filewrite_filewrite_not_iterable_raises():
    """Not iterable fileWrite raises."""
    context = Context({
        'k1': 'v1',
        'fileWrite': 1})

    with pytest.raises(ContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWrite'] must exist, be iterable "
        "and contain 'path' for pypyr.steps.filewrite. argument of type "
        "'int' is not iterable")


def test_filewrite_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fileWrite': {
            'path': ''
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWrite']['path'] must have a value for "
        "pypyr.steps.filewrite.")


def test_filewrite_none_path_raises():
    """Empty path raises."""
    context = Context({
        'fileWrite': {
            'path': None
        }})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == (
        "context['fileWrite']['path'] must have a value for "
        "pypyr.steps.filewrite.")


def test_filewrite_no_path_raises():
    """No path raises."""
    context = Context({
        'fileWrite': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == ("context['fileWrite']['path'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filewrite.")


def test_filewrite_no_payload_raises():
    """No payload raises."""
    context = Context({
        'fileWrite': {
            'path': 'arb'
        }})

    with pytest.raises(KeyNotInContextError) as err_info:
        filewrite.run_step(context)

    assert str(err_info.value) == ("context['fileWrite']['payload'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filewrite.")
# endregion validation

# region write text


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_payload(mock_path):
    """Success case writes only specific context payload."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': "one\ntwo\nthree"
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'v1'
    assert context['fileWrite'] == {'path': '/arb/blah',
                                    'payload': "one\ntwo\nthree"}

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_payload_encoding(mock_path):
    """Success case writes only specific context payload and encoding."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': 'one\ntwo\nthree',
            'encoding': 'arb'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'v1'
    assert context['fileWrite'] == {'path': '/arb/blah',
                                    'payload': 'one\ntwo\nthree',
                                    'encoding': 'arb'}

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding='arb')

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_encoding_from_config_override(mock_path,
                                                      monkeypatch):
    """Direct encoding overrides config encoding.."""
    monkeypatch.setattr('pypyr.config.config.default_encoding', 'arbx')
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': 'one\ntwo\nthree',
            'encoding': 'arb'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'v1'
    assert context['fileWrite'] == {'path': '/arb/blah',
                                    'payload': 'one\ntwo\nthree',
                                    'encoding': 'arb'}

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding='arb')

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_encoding_from_config(mock_path,
                                             monkeypatch):
    """Encoding comes from config."""
    monkeypatch.setattr('pypyr.config.config.default_encoding', 'arbx')
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': 'one\ntwo\nthree'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'v1'
    assert context['fileWrite'] == {'path': '/arb/blah',
                                    'payload': 'one\ntwo\nthree'}

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding='arbx')

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_non_string_payload(mock_path):
    """Empty payload write non string types to file."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': 123
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == '123'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_empty_payload(mock_path):
    """Empty payload write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': ''
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == ''


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_none_payload(mock_path):
    """None payload write empty file."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': None
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == 'None'

# endregion write text
# region append


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_append(mock_path):
    """Append to file."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': "one\ntwo\nthree",
            'append': True,
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'a', encoding=None)

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_append_false(mock_path):
    """Open in write mode when append explicitly False."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': "one\ntwo\nthree",
            'append': False,
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == 'one\ntwo\nthree'

# endregion append

# region binary


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_binary(mock_path):
    """Write binary data."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': b"one\ntwo\nthree",
            'binary': True,
        }})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        payload = out_bytes.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'wb', encoding=None)

    assert payload == b'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_binary_false(mock_path):
    """Open in write mode when binary explicitly False."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': "one\ntwo\nthree",
            'binary': False,
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == 'one\ntwo\nthree'

# endregion binary

# region binary + append


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_binary_append(mock_path):
    """Append binary data."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': b"one\ntwo\nthree",
            'binary': True,
            'append': True
        }})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        payload = out_bytes.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'ab', encoding=None)

    assert payload == b'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_binary_true_append_false(mock_path):
    """Write binary data with append explicit False."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': b"one\ntwo\nthree",
            'binary': True,
            'append': False
        }})

    with io.BytesIO() as out_bytes:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            filewrite.run_step(context)

        payload = out_bytes.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'wb', encoding=None)

    assert payload == b'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_binary_false_append_true(mock_path):
    """Open in append mode when binary explicitly False."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': "one\ntwo\nthree",
            'binary': False,
            'append': True
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'a', encoding=None)

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_binary_false_append_false(mock_path):
    """Open in write mode when binary & append explicitly False."""
    context = Context({
        'k1': 'v1',
        'fileWrite': {
            'path': '/arb/blah',
            'payload': "one\ntwo\nthree",
            'binary': False,
            'append': False
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/blah')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == 'one\ntwo\nthree'

# endregion binary + append

# region substitutions


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_substitutions(mock_path):
    """Success case writes only specified context with substitutions."""
    context = Context({
        'k1': 'v1',
        'p': '/arb/path',
        'intkey': 3,
        'is_bin': True,
        'is_append': True,
        'enc': 'arb',
        'fileWrite': {
            'path': '{p}',
            'payload': 'begin {k1} {intkey} end',
            'binary': '{is_bin}',
            'append': '{is_append}',
            'encoding': '{enc}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['k1'] == 'v1'
    assert context['fileWrite'] == {
        'path': '{p}',
        'payload': 'begin {k1} {intkey} end',
        'binary': '{is_bin}',
        'append': '{is_append}',
        'encoding': '{enc}'
    }

    mock_path.assert_called_once_with('/arb/path')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'ab', encoding='arb')

    assert payload == 'begin v1 3 end'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_substitutions_bare_payload(mock_path):
    """Write bare formatting expression as payload."""
    context = Context({
        'k1': 'v1',
        'p': '/arb/path',
        'out': 'one\ntwo\nthree',
        'is_append': False,
        'fileWrite': {
            'path': '{p}',
            'payload': '{out}',
            'append': '{is_append}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['k1'] == 'v1'
    assert context['fileWrite'] == {
        'path': '{p}',
        'payload': '{out}',
        'append': '{is_append}'
    }

    mock_path.assert_called_once_with('/arb/path')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == 'one\ntwo\nthree'


@patch('pypyr.steps.filewrite.Path')
def test_filewrite_pass_with_non_string_substitutions(mock_path):
    """Convert non-string to str on text write with substitution."""
    context = Context({
        'k1': 'v1',
        'p': '/arb/path',
        'intkey': 123,
        'is_bin': False,
        'is_append': 0,
        'fileWrite': {
            'path': '{p}',
            'payload': '{intkey}',
            'binary': '{is_bin}',
            'append': '{is_append}'
        }})

    with io.StringIO() as out_text:
        with patch('pypyr.steps.filewrite.open',
                   mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_text.write
            filewrite.run_step(context)

        payload = out_text.getvalue()

    mock_path.assert_called_once_with('/arb/path')
    mocked_path = mock_path.return_value
    mocked_path.parent.mkdir.assert_called_once_with(parents=True,
                                                     exist_ok=True)
    mock_output.assert_called_once_with(mocked_path, 'w', encoding=None)

    assert payload == '123'
# endregion substitutions
