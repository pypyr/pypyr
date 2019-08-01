"""debug.py unit tests."""
import logging
from unittest.mock import call
from pypyr.context import Context
import pypyr.steps.debug as debug
from tests.common.utils import patch_logger


def test_no_inputs():
    """Dump entire context with no input specified."""
    context = Context({'k1': 'v1', 'k2': 'x{k1}x', 'k3': [0, 1, 2]})

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('\n'
             '{\n'
             '  "k1": "v1",\n'
             '  "k2": "x{k1}x",\n'
             '  "k3": [\n'
             '    0,\n'
             '    1,\n'
             '    2\n'
             '  ]\n'
             '}')]


def test_no_keys_with_formatting():
    """Dump entire context with no keys but with formatting."""
    context = Context({'k1': 'v1',
                       'k2': 'x{k1}x',
                       'k3': [0, 1, 2],
                       'debug': {'format': True}
                       })

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('\n'
             '{\n'
             '  "k1": "v1",\n'
             '  "k2": "xv1x",\n'
             '  "k3": [\n'
             '    0,\n'
             '    1,\n'
             '    2\n'
             '  ],\n'
             '  "debug": {\n'
             '    "format": true\n'
             '  }\n'
             '}')]


def test_key_str():
    """Dump single key without formatting."""
    context = Context({'k1': 'v1',
                       'k2': 'x{k1}x',
                       'k3': [0, 1, 2],
                       'debug': {'keys': 'k2'}
                       })

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('\n'
             '{\n'
             '  "k2": "x{k1}x"\n'
             '}')]


def test_key_str_format():
    """Dump single key with formatting."""
    context = Context({'k1': 'v1',
                       'k2': 'x{k1}x',
                       'k3': [0, 1, 2],
                       'debug': {'keys': 'k2', 'format': True}
                       })

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('\n'
             '{\n'
             '  "k2": "xv1x"\n'
             '}')]


def test_keys_list():
    """Dump list of keys without formatting."""
    context = Context({'k1': 'v1',
                       'k2': 'x{k1}x',
                       'k3': [0, 1, 2],
                       'debug': {'keys': ['k1', 'k2']}
                       })

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('\n'
             '{\n'
             '  "k1": "v1",\n'
             '  "k2": "x{k1}x"\n'
             '}')]


def test_keys_list_format():
    """Dump list of keys with formatting."""
    context = Context({'k1': 'v1',
                       'k2': 'x{k1}x',
                       'k3': [0, 1, 2],
                       'debug': {'keys': ['k1', 'k2'], 'format': True}
                       })

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('\n'
             '{\n'
             '  "k1": "v1",\n'
             '  "k2": "xv1x"\n'
             '}')]
