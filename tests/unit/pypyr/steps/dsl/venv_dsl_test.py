"""Unit tests for pypyr.steps.dsl.venv."""
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch, call, DEFAULT

import pytest

from pypyr.context import Context
from pypyr.errors import ContextError, KeyNotInContextError, MultiError
from pypyr.steps.dsl.venv import (
    EXCEPTION_INPUT,
    EXCEPTION_LIST_INPUT,
    VenvCreatorStep)


def get_simple_context():
    """Create a test SimpleNamespace to serve as EnvBuilder context."""
    context = SimpleNamespace()
    context.env_exec_cmd = '/python'
    context.bin_path = '/venv/bin'
    context.env_dir = '/venv'
    return context


def test_venv_dsl_no_config_key():
    """Raise error when required venv key missing."""
    with pytest.raises(KeyNotInContextError) as err:
        VenvCreatorStep.from_context(Context({'a': 'b'}))

    assert str(err.value) == (
        "context['venv'] doesn't exist. "
        + "It must exist for pypyr.steps.venv.")


def test_venv_dsl_context_wrong_type():
    """Raise error when required venv is wrong type."""
    with pytest.raises(ContextError) as err:
        VenvCreatorStep.from_context(Context({'venv': 123}))

    assert str(err.value) == EXCEPTION_INPUT.format(bad_type='int')


def test_venv_dsl_context_list_contains_wrong_type():
    """Raise error when required venv is list with a wrong type."""
    with pytest.raises(ContextError) as err:
        VenvCreatorStep.from_context(Context({'venv': ['/arb', 123]}))

    assert str(err.value) == EXCEPTION_LIST_INPUT.format(bad_type='int')


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_simple_str(mock_builder):
    """Run with simple str input."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context({'venv': '/arb'}))

    expected_path = str(Path('/arb').expanduser().resolve())
    assert len(step.venvs) == 1
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path

    step.run_step()

    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_called_once_with(context)
    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_mapping_simple_str(mock_builder):
    """Run with simple str input inside mapping."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context(
        {'venv': {
            'path': '/arb'}}))

    expected_path = str(Path('/arb').expanduser().resolve())
    assert len(step.venvs) == 1
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path

    step.run_step()

    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_called_once_with(context)
    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_mapping_list_of_str(mock_builder):
    """Run with list of str input inside mapping."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context(
        {'venv': {
            'path': ['/arb1', '/arb2']}}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())

    assert len(step.venvs) == 2
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    assert mock_builder.call_count == 2

    step.run_step()

    assert mocked_builder.create.call_count == 2
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2)])

    assert mocked_builder.upgrade_dependencies.call_count == 2
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)

    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_list_of_str(mock_builder):
    """Run with list of str input."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context(
        {'venv': ['/arb1', '/arb2']}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())

    assert len(step.venvs) == 2
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    assert mock_builder.call_count == 2

    step.run_step()

    assert mocked_builder.create.call_count == 2
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2)])

    assert mocked_builder.upgrade_dependencies.call_count == 2
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)

    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_list_of_str_and_mapping(mock_builder):
    """Run with list of str and mapping mixed input."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context(
        {'venv': ['/arb1',
                  {'path': '/arb2'}]}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())

    assert len(step.venvs) == 2
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    assert mock_builder.call_count == 2

    step.run_step()

    assert mocked_builder.create.call_count == 2
    assert sorted(mocked_builder.create.mock_calls) == sorted([
        call(expected_path1),
        call(expected_path2)])

    assert mocked_builder.upgrade_dependencies.call_count == 2
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)

    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_list_of_str_and_mapping_list(mock_builder):
    """Run with list of str and mapping containing list path mixed input."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context(
        {'venv': ['/arb1',
                  {'path': ['/arb2', '/arb3']}]}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())
    expected_path3 = str(Path('/arb3').expanduser().resolve())

    assert len(step.venvs) == 3
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    venv_creator = step.venvs[2]
    assert venv_creator.path == expected_path3

    assert mock_builder.call_count == 3

    step.run_step()

    assert mocked_builder.create.call_count == 3
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2),
         call(expected_path3)])

    assert mocked_builder.upgrade_dependencies.call_count == 3
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[2] == call(context)

    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_list_of_str_and_mapping_list_no_pip(mock_builder):
    """Run with with_pip False does not install dependencies."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    step = VenvCreatorStep.from_context(Context(
        {'venv': ['/arb1',
                  {'path': ['/arb2', '/arb3'],
                   'with_pip': False}]}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())
    expected_path3 = str(Path('/arb3').expanduser().resolve())

    assert len(step.venvs) == 3
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    venv_creator = step.venvs[2]
    assert venv_creator.path == expected_path3

    assert mock_builder.call_count == 3

    step.run_step()

    assert mocked_builder.create.call_count == 3
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2),
         call(expected_path3)])

    mocked_builder.upgrade_dependencies.assert_called_once_with(context)

    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_simple_str_error(mock_builder):
    """Run with simple str input raising error on create."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context
    mocked_builder.create.side_effect = ValueError('arb')

    step = VenvCreatorStep.from_context(Context({'venv': '/arb'}))

    expected_path = str(Path('/arb').expanduser().resolve())

    assert len(step.venvs) == 1
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path

    with pytest.raises(ValueError) as err:
        step.run_step()

    assert str(err.value) == 'arb'

    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_not_called()
    mocked_builder.pip_install_extras.assert_not_called()


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_mapping_list_of_str_error_on_create(mock_builder):
    """Run with list of str input inside mapping raising create errors."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context
    mocked_builder.create.side_effect = [DEFAULT,
                                         ValueError('arb'),
                                         DEFAULT,
                                         ValueError('arb2')]

    step = VenvCreatorStep.from_context(Context(
        {'venv': {
            'path': ['/arb1', '/arb2', '/arb3', '/arb4'],
            'pip': 'package1 package2'}}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())
    expected_path3 = str(Path('/arb3').expanduser().resolve())
    expected_path4 = str(Path('/arb4').expanduser().resolve())

    assert len(step.venvs) == 4
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    venv_creator = step.venvs[2]
    assert venv_creator.path == expected_path3

    venv_creator = step.venvs[3]
    assert venv_creator.path == expected_path4

    assert mock_builder.call_count == 4

    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value.errors) == 2
    assert repr(err.value.errors[0]) == repr(ValueError('arb'))
    assert repr(err.value.errors[1]) == repr(ValueError('arb2'))

    assert mocked_builder.create.call_count == 4
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2),
         call(expected_path3),
         call(expected_path4)])

    assert mocked_builder.upgrade_dependencies.call_count == 2
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)

    assert mocked_builder.pip_install_extras.call_count == 2
    assert mocked_builder.pip_install_extras.mock_calls[0] == call(
        'package1 package2')
    assert mocked_builder.pip_install_extras.mock_calls[1] == call(
        'package1 package2')


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_list_of_mapping_error_on_create(mock_builder):
    """Run with input list of mapping varying pip raising create errors."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context
    mocked_builder.create.side_effect = [DEFAULT,
                                         ValueError('arb'),
                                         DEFAULT,
                                         ValueError('arb2')]

    step = VenvCreatorStep.from_context(Context(
        {'venv': [
            {'path': '/arb1',
             'pip': 'package1 package2'},
            {'path': '/arb2',
             'pip': 'package3 package4'},
            {'path': '/arb3',
             'pip': 'package5 package6'},
            {'path': '/arb4',
             'pip': 'package7 package8'},
        ]}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())
    expected_path3 = str(Path('/arb3').expanduser().resolve())
    expected_path4 = str(Path('/arb4').expanduser().resolve())

    assert len(step.venvs) == 4
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    venv_creator = step.venvs[2]
    assert venv_creator.path == expected_path3

    venv_creator = step.venvs[3]
    assert venv_creator.path == expected_path4

    assert mock_builder.call_count == 4

    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value.errors) == 2
    assert repr(err.value.errors[0]) == repr(ValueError('arb'))
    assert repr(err.value.errors[1]) == repr(ValueError('arb2'))

    assert mocked_builder.create.call_count == 4
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2),
         call(expected_path3),
         call(expected_path4)])

    assert mocked_builder.upgrade_dependencies.call_count == 2
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)

    assert mocked_builder.pip_install_extras.call_count == 2
    assert mocked_builder.pip_install_extras.mock_calls[0] == call(
        'package1 package2')
    assert mocked_builder.pip_install_extras.mock_calls[1] == call(
        'package5 package6')


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_dsl_mapping_list_of_str_error_on_pip_install(mock_builder):
    """Run with list of str input inside mapping raising extras pip errors."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context
    mocked_builder.pip_install_extras.side_effect = [DEFAULT,
                                                     ValueError('arb'),
                                                     DEFAULT,
                                                     ValueError('arb2')]

    step = VenvCreatorStep.from_context(Context(
        {'venv': [
            {'path': '/arb1',
             'pip': 'package1 package2'},
            {'path': '/arb2',
             'pip': 'package3 package4'},
            {'path': '/arb3',
             'pip': 'package5 package6'},
            {'path': '/arb4',
             'pip': 'package7 package8'},
        ]}))

    expected_path1 = str(Path('/arb1').expanduser().resolve())
    expected_path2 = str(Path('/arb2').expanduser().resolve())
    expected_path3 = str(Path('/arb3').expanduser().resolve())
    expected_path4 = str(Path('/arb4').expanduser().resolve())

    assert len(step.venvs) == 4
    venv_creator = step.venvs[0]
    assert venv_creator.path == expected_path1

    venv_creator = step.venvs[1]
    assert venv_creator.path == expected_path2

    venv_creator = step.venvs[2]
    assert venv_creator.path == expected_path3

    venv_creator = step.venvs[3]
    assert venv_creator.path == expected_path4

    assert mock_builder.call_count == 4

    with pytest.raises(MultiError) as err:
        step.run_step()

    assert len(err.value.errors) == 2
    assert repr(err.value.errors[0]) == repr(ValueError('arb'))
    assert repr(err.value.errors[1]) == repr(ValueError('arb2'))

    assert mocked_builder.create.call_count == 4
    assert sorted(mocked_builder.create.mock_calls) == sorted(
        [call(expected_path1),
         call(expected_path2),
         call(expected_path3),
         call(expected_path4)])

    assert mocked_builder.upgrade_dependencies.call_count == 4
    assert mocked_builder.upgrade_dependencies.mock_calls[0] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[1] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[2] == call(context)
    assert mocked_builder.upgrade_dependencies.mock_calls[3] == call(context)

    assert mocked_builder.pip_install_extras.call_count == 4
    assert mocked_builder.pip_install_extras.mock_calls[0] == call(
        'package1 package2')
    assert mocked_builder.pip_install_extras.mock_calls[1] == call(
        'package3 package4')
    assert mocked_builder.pip_install_extras.mock_calls[2] == call(
        'package5 package6')
    assert mocked_builder.pip_install_extras.mock_calls[3] == call(
        'package7 package8')
