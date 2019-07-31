"""glob.py unit tests."""
import logging
import pytest
from unittest.mock import patch
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.glob as glob_step
from tests.common.utils import patch_logger


def test_glob_no_input_raises():
    """No input context raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        glob_step.run_step(context)

    assert str(err_info.value) == ("context['glob'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.glob.")


def test_glob_empty_path_raises():
    """Empty input raises."""
    context = Context({
        'glob': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        glob_step.run_step(context)

    assert str(err_info.value) == ("context['glob'] must have a "
                                   "value for pypyr.steps.glob.")


def test_glob_empty_string_path_raises():
    """Empty string glob raises."""
    context = Context({
        'glob': ''})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        glob_step.run_step(context)

    assert str(err_info.value) == ("The glob path is an empty str")


def test_glob_empty_path_list_raises():
    """Empty glob list raises."""
    context = Context({
        'glob': []})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        glob_step.run_step(context)

    assert str(err_info.value) == ("The glob list has an empty str")


def test_glob_list_with_empty_raises():
    """Glob list with missing item raises."""
    context = Context({
        'glob': ['a', '', 'c']})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        glob_step.run_step(context)

    assert str(err_info.value) == ("The glob list has an empty str")


@patch('pypyr.utils.filesystem.get_glob')
def test_glob_single(mock_glob):
    """Single path ok."""
    context = Context({
        'ok1': 'ov1',
        'glob': './arb/x'})

    mock_glob.return_value = ['./foundfile']

    with patch_logger('pypyr.steps.glob', logging.INFO) as mock_logger_info:
        glob_step.run_step(context)

    mock_logger_info.assert_called_once_with(
        'glob checked 1 globs and saved 1 paths to globOut')
    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['glob'] == './arb/x'
    assert context["globOut"] == ['./foundfile']

    mock_glob.assert_called_once_with('./arb/x')


@patch('pypyr.utils.filesystem.get_glob')
def test_glob_single_not_found(mock_glob):
    """Single path ok on not found."""
    context = Context({
        'ok1': 'ov1',
        'glob': './arb/x'})

    mock_glob.return_value = []

    with patch_logger(
            'pypyr.steps.glob', logging.INFO) as mock_logger_info:
        glob_step.run_step(context)

    mock_logger_info.assert_called_once_with(
        'glob checked 1 globs and saved 0 paths to globOut')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['glob'] == './arb/x'
    assert context["globOut"] == []

    mock_glob.assert_called_once_with('./arb/x')


@patch('pypyr.utils.filesystem.get_glob')
def test_glob_single_with_formatting(mock_glob):
    """Single path ok with string formatting."""
    context = Context({
        'ok1': 'ov1',
        'glob': './{ok1}/x'})

    mock_glob.return_value = ['./foundfile']

    glob_step.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['glob'] == './{ok1}/x'
    assert context["globOut"] == ['./foundfile']

    mock_glob.assert_called_once_with('./ov1/x')


@patch('pypyr.utils.filesystem.get_glob', autospec=True)
def test_glob_list(mock_glob):
    """Multiple paths ok."""
    context = Context({
        'ok1': 'ov1',
        'glob': ['./arb/x', './arb/y', './arb/z']})

    mock_glob.return_value = [
        './f1.1',
        './f2.1',
        './f2.2',
        './f2.3',
    ]

    with patch_logger('pypyr.steps.glob', logging.INFO) as mock_logger_info:
        glob_step.run_step(context)

    mock_logger_info.assert_called_once_with(
        'glob checked 3 globs and saved 4 paths to globOut')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['glob'] == ['./arb/x', './arb/y', './arb/z']
    assert context["globOut"] == [
        './f1.1',
        './f2.1',
        './f2.2',
        './f2.3',
    ]

    mock_glob.assert_called_once_with(
        ['./arb/x', './arb/y', './arb/z'])


@patch('pypyr.utils.filesystem.get_glob')
def test_glob_list_none(mock_glob):
    """Multiple paths ok with none returning match."""
    context = Context({
        'ok1': 'ov1',
        'glob': ['./{ok1}/x', './arb/{ok1}', '{ok1}/arb/z']})

    mock_glob.return_value = []

    with patch_logger('pypyr.steps.glob', logging.INFO) as mock_logger_info:
        glob_step.run_step(context)

    mock_logger_info.assert_called_once_with(
        'glob checked 3 globs and saved 0 paths to globOut')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['glob'] == ['./{ok1}/x', './arb/{ok1}', '{ok1}/arb/z']
    assert context["globOut"] == []

    mock_glob.assert_called_once_with(['./ov1/x',
                                       './arb/ov1',
                                       'ov1/arb/z'])
