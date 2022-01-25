"""fileread.py unit tests."""
from unittest.mock import mock_open, patch

import pytest

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileread as fileread


def test_fileread_no_input_raises():
    """No input."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileread.")


def test_fileread_none_raises():
    """Input exists but is None."""
    context = Context({
        'k1': 'v1',
        'fileRead': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead'] must have a "
                                   "value for pypyr.steps.fileread.")


def test_fileread_none_path_raises():
    """None path raises."""
    context = Context({
        'fileRead': {
            'path': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead']['path'] must have a "
                                   "value for pypyr.steps.fileread.")


def test_fileread_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fileRead': {
            'path': ''}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead']['path'] must have a "
                                   "value for pypyr.steps.fileread.")


def test_fileread_no_key_raises():
    """No key raises."""
    context = Context({
        'fileRead': {
            'path': '/arb'}})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead']['key'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileread.")


def test_fileread_none_key_raises():
    """None key raises."""
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead']['key'] must have a "
                                   "value for pypyr.steps.fileread.")


def test_fileread_empty_key_raises():
    """Empty key raises."""
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': ''}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileread.run_step(context)

    assert str(err_info.value) == ("context['fileRead']['key'] must have a "
                                   "value for pypyr.steps.fileread.")

# endregion validation

# region text mode


def test_fileread_defaults():
    """Read file with minimal defaults."""
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': 'out'}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data='one\ntwo\nthree')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == 'one\ntwo\nthree'

    mocked_open.assert_called_once_with('/arb', 'r', encoding=None)


def test_fileread_defaults_with_encoding(monkeypatch):
    """Read file with minimal defaults and encoding set by config."""
    monkeypatch.setattr('pypyr.config.config.default_encoding', 'arbe')
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': 'out'}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data='one\ntwo\nthree')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == 'one\ntwo\nthree'

    mocked_open.assert_called_once_with('/arb', 'r', encoding='arbe')


def test_fileread_all():
    """Read file with all args."""
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': 'out',
            'encoding': 'arb'}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data='one\ntwo\nthree')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == 'one\ntwo\nthree'

    mocked_open.assert_called_once_with('/arb', 'r', encoding='arb')


def test_fileread_all_encoding_override(monkeypatch):
    """Read file with all args, overriding config encoding."""
    monkeypatch.setattr('pypyr.config.config.default_encoding', 'XXX')
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': 'out',
            'encoding': 'arb'}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data='one\ntwo\nthree')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == 'one\ntwo\nthree'

    mocked_open.assert_called_once_with('/arb', 'r', encoding='arb')

# endregion text mode

# region binary mode


def test_fileread_binary_true():
    """Read file with binary true."""
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': 'out',
            'binary': True}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data=b'12345')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == b'12345'

    mocked_open.assert_called_once_with('/arb', 'rb', encoding=None)


def test_fileread_binary_explicit_false():
    """Read file with binary explicit false."""
    context = Context({
        'fileRead': {
            'path': '/arb',
            'key': 'out',
            'binary': False}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data='one\ntwo\nthree')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == 'one\ntwo\nthree'

    mocked_open.assert_called_once_with('/arb', 'r', encoding=None)

# endregion binary mode

# region substitutions


def test_fileread_substitutions():
    """Read file with substitutions."""
    context = Context({
        'p': '/arb',
        'k': 'out',
        'b': False,
        'c': 'arb',
        'fileRead': {
            'path': '{p}',
            'key': '{k}',
            'binary': '{b}',
            'encoding': '{c}'}})

    with patch('pypyr.steps.fileread.open',
               mock_open(read_data='one\ntwo\nthree')) as mocked_open:
        fileread.run_step(context)

    assert context['out'] == 'one\ntwo\nthree'

    assert context == {
        'p': '/arb',
        'k': 'out',
        'b': False,
        'c': 'arb',
        'out': 'one\ntwo\nthree',
        'fileRead': {
            'path': '{p}',
            'key': '{k}',
            'binary': '{b}',
            'encoding': '{c}'}}

    mocked_open.assert_called_once_with('/arb', 'r', encoding='arb')

# endregion substitutions
