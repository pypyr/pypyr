"""Unit tests for pypyr.steps.venv.

Most of the testing happens in pypyr.steps.dsl.venv & pypyr.venv.

All this needs to test is that the step calls through to the underlying core.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pypyr.context import Context
from pypyr.steps import venv


def get_simple_context():
    """Create a test SimpleNamespace to serve as EnvBuilder context."""
    context = SimpleNamespace()
    context.env_exec_cmd = '/python'
    context.bin_path = '/venv/bin'
    context.env_dir = '/venv'
    return context


@patch('pypyr.venv.EnvBuilderWithExtraDeps')
def test_venv_create(mock_builder):
    """Create a venv calls through to the venv dsl."""
    context = get_simple_context()
    mocked_builder = mock_builder.return_value
    mocked_builder.context = context

    venv.run_step(Context({'venv': '/arb'}))

    expected_path = str(Path('/arb').expanduser().resolve())

    mocked_builder.create.assert_called_once_with(expected_path)
    mocked_builder.upgrade_dependencies.assert_called_once_with(context)
    mocked_builder.pip_install_extras.assert_not_called()
