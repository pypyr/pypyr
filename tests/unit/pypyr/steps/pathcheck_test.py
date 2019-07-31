"""pathcheck.py unit tests."""
import logging
import pytest
from unittest.mock import call, patch
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.pathcheck as pathchecker
from tests.common.utils import patch_logger


def test_pathcheck_no_input_raises():
    """No input context raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        pathchecker.run_step(context)

    assert str(err_info.value) == ("context['pathCheck'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.pathcheck.")


def test_pathcheck_empty_path_raises():
    """Empty path check raises."""
    context = Context({
        'pathCheck': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        pathchecker.run_step(context)

    assert str(err_info.value) == ("context['pathCheck'] must have a "
                                   "value for pypyr.steps.pathcheck.")


def test_pathcheck_empty_string_path_raises():
    """Empty string path check raises."""
    context = Context({
        'pathCheck': ''})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        pathchecker.run_step(context)

    assert str(err_info.value) == ("context['pathCheck'] must have a "
                                   "value for pypyr.steps.pathcheck.")


def test_pathcheck_empty_path_list_raises():
    """Empty path check list raises."""
    context = Context({
        'pathCheck': []})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        pathchecker.run_step(context)

    assert str(err_info.value) == ("context['pathCheck'] must have a "
                                   "value for pypyr.steps.pathcheck.")


@patch('pypyr.utils.filesystem.get_glob')
def test_pathcheck_single(mock_glob):
    """Single path ok."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': './arb/x'})

    mock_glob.return_value = ['./foundfile']

    with patch_logger(
            'pypyr.steps.pathcheck', logging.INFO) as mock_logger_info:
        pathchecker.run_step(context)

    mock_logger_info.assert_called_once_with('checked 1 path(s) and found 1')
    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == './arb/x'
    assert context["pathCheckOut"] == {'./arb/x': {
        'exists': True,
        'count': 1,
        'found': ['./foundfile']
    }}

    mock_glob.assert_called_once_with('./arb/x')


@patch('pypyr.utils.filesystem.get_glob')
def test_pathcheck_single_not_found(mock_glob):
    """Single path ok on not found."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': './arb/x'})

    mock_glob.return_value = []

    with patch_logger(
            'pypyr.steps.pathcheck', logging.INFO) as mock_logger_info:
        pathchecker.run_step(context)

    mock_logger_info.assert_called_once_with('checked 1 path(s) and found 0')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == './arb/x'
    assert context["pathCheckOut"] == {'./arb/x': {
        'exists': False,
        'count': 0,
        'found': []
    }}

    mock_glob.assert_called_once_with('./arb/x')


@patch('pypyr.utils.filesystem.get_glob')
def test_pathcheck_single_with_formatting(mock_glob):
    """Single path ok with string formatting."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': './{ok1}/x'})

    mock_glob.return_value = ['./foundfile']

    pathchecker.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == './{ok1}/x'
    assert context["pathCheckOut"] == {'./{ok1}/x': {
        'exists': True,
        'count': 1,
        'found': ['./foundfile']
    }}

    mock_glob.assert_called_once_with('./ov1/x')


@patch('pypyr.utils.filesystem.get_glob')
def test_pathcheck_list(mock_glob):
    """Multiple paths ok with some returning no match."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': ['./arb/x', './arb/y', './arb/z']})

    mock_glob.side_effect = [
        ['./f1.1'],
        ['./f2.1', './f2.2', './f2.3'],
        []
    ]

    with patch_logger(
            'pypyr.steps.pathcheck', logging.INFO) as mock_logger_info:
        pathchecker.run_step(context)

    mock_logger_info.assert_called_once_with('checked 3 path(s) and found 4')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == ['./arb/x', './arb/y', './arb/z']
    assert context["pathCheckOut"] == {
        './arb/x': {
            'exists': True,
            'count': 1,
            'found': ['./f1.1']
        },
        './arb/y': {
            'exists': True,
            'count': 3,
            'found': ['./f2.1', './f2.2', './f2.3']
        },
        './arb/z': {
            'exists': False,
            'count': 0,
            'found': []
        },
    }

    assert mock_glob.mock_calls == [call('./arb/x'),
                                    call('./arb/y'),
                                    call('./arb/z')]


@patch('pypyr.utils.filesystem.get_glob')
def test_pathcheck_list_none(mock_glob):
    """Multiple paths ok with none returning match."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': ['./{ok1}/x', './arb/{ok1}', '{ok1}/arb/z']})

    mock_glob.side_effect = [
        [],
        [],
        []
    ]

    with patch_logger(
            'pypyr.steps.pathcheck', logging.INFO) as mock_logger_info:
        pathchecker.run_step(context)

    mock_logger_info.assert_called_once_with('checked 3 path(s) and found 0')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == ['./{ok1}/x', './arb/{ok1}', '{ok1}/arb/z']
    assert context["pathCheckOut"] == {
        './{ok1}/x': {
            'exists': False,
            'count': 0,
            'found': []
        },
        './arb/{ok1}': {
            'exists': False,
            'count': 0,
            'found': []
        },
        '{ok1}/arb/z': {
            'exists': False,
            'count': 0,
            'found': []
        },
    }

    assert mock_glob.mock_calls == [call('./ov1/x'),
                                    call('./arb/ov1'),
                                    call('ov1/arb/z')]
