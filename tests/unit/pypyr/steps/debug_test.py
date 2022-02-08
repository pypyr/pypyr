"""debug.py unit tests."""
import datetime
import logging
from collections import OrderedDict
from unittest.mock import call, patch
import sys

from pypyr.context import Context
import pypyr.steps.debug as debug
from pypyr.dsl import Jsonify, PyString, SicString
from tests.common.utils import patch_logger

is_windows = sys.platform.startswith("win")


def test_no_inputs():
    """Dump entire context with no input specified."""
    context = Context({'k1': 'v1', 'k2': 'x{k1}x', 'k3': [0, 1, 2]})

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call("\n{'k1': 'v1', 'k2': 'x{k1}x', 'k3': [0, 1, 2]}")]


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
        call("\n{'debug': {'format': True}, 'k1': 'v1', "
             "'k2': 'xv1x', 'k3': [0, 1, 2]}")]


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
        call("\n{'k2': 'x{k1}x'}")]


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
        call("\n{'k2': 'xv1x'}")]


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
        call("\n{'k1': 'v1', 'k2': 'x{k1}x'}")]


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
        call("\n{'k1': 'v1', 'k2': 'xv1x'}")]


def test_recursive():
    """Dump of the recursive objects must not fail."""
    arb_list = ['ham', 'eggs']
    arb_list.append(arb_list)

    context = Context({'k1': arb_list})

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call("\n"
             "{'k1': ['ham', 'eggs',"
             f" <Recursion on list with id={id(arb_list)}>]}}")]


def test_key_sorting():
    """Dict keys represented alphabetically."""
    context = Context(
        {
            'k2': 'v2',
            'k1': {'z': 'vz', 'a': 'va'}
        }
    )

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call("\n{'k1': {'a': 'va', 'z': 'vz'}, 'k2': 'v2'}")]


def test_multiline():
    """Check line breaks at large objects."""
    context = Context(
        {
            'key1': 'value1',
            'key2': 'value2',
            'key3': {
                'extra_large_key_name': 'with_extra_ordinary_key_value'
            },
        }
    )

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [
        call("\n"
             "{'key1': 'value1',\n"
             " 'key2': 'value2',\n"
             " 'key3': {'extra_large_key_name': "
             "'with_extra_ordinary_key_value'}}")]


def get_obj_hex(obj):
    """Get platform appropriate object hex."""
    if is_windows:
        return f'0x{id(obj):0{16}X}'
    else:
        return hex(id(obj))


def test_complex_object():
    """Check different complex objects, like error, date, type..."""
    py_str = PyString('py_arb')

    def arb_func():
        pass

    # autopep8: off
    # ignore flake warning to check lambda address
    arb_lambda = lambda x: x  # noqa: E731
    # autopep8: on

    context = Context({
        'bound_method': py_str.get_value,
        'date': datetime.date(2019, 10, 10),
        'datetime': datetime.datetime(2019, 10, 10),
        'exception': ValueError("Test", 'exc_arg'),
        'func': arb_func,
        'jsonify': Jsonify('jsonify arb'),
        'lambda': arb_lambda,
        'list': ['arb1', 'arb2', ['arb3']],
        'ordered_dict': OrderedDict({'a': 1, 'b': 2}),
        'py': py_str,
        'sic': SicString('sic_arb'),
        'tuple': ('arb1', 'arb2',),
        'type': ValueError,
    })

    with patch_logger('pypyr.steps.debug', logging.INFO) as mock_logger_info:
        debug.run_step(context)

    assert mock_logger_info.mock_calls == [call(
        "\n"
        "{'bound_method': <bound method PyString.get_value "
        "of PyString('py_arb')>,\n"
        " 'date': datetime.date(2019, 10, 10),\n"
        " 'datetime': datetime.datetime(2019, 10, 10, 0, 0),\n"
        " 'exception': ValueError('Test', 'exc_arg'),\n"
        " 'func': <function test_complex_object.<locals>.arb_func"
        f" at {get_obj_hex(arb_func)}>,\n"
        " 'jsonify': Jsonify('jsonify arb'),\n"
        " 'lambda': <function test_complex_object.<locals>.<lambda>"
        f" at {get_obj_hex(arb_lambda)}>,\n"
        " 'list': ['arb1', 'arb2', ['arb3']],\n"
        " 'ordered_dict': OrderedDict([('a', 1), ('b', 2)]),\n"
        " 'py': PyString('py_arb'),\n"
        " 'sic': SicString('sic_arb'),\n"
        " 'tuple': ('arb1', 'arb2'),\n"
        " 'type': <class 'ValueError'>}")]


@patch("pprint.pformat")
def test_pformat_called_when_logging_is_enabled(mock_pformat):
    """Check that pformat called only when logging is enabled."""
    ctx = Context({"k1": "v1"})
    debug.run_step(ctx)
    mock_pformat.assert_called_once_with(ctx)


@patch("pprint.pformat")
def test_pformat_not_called_when_logging_is_disabled(mock_pformat):
    """Check that pformat not called only when logging is disabled."""
    ctx = Context({"k1": "v1"})

    logging_level = debug.logger.level
    debug.logger.setLevel(logging.WARNING)
    try:
        debug.run_step(ctx)
    finally:
        debug.logger.setLevel(logging_level)

    mock_pformat.assert_not_called()
