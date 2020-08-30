"""cof.py unit tests."""
import logging
import pytest
from pypyr.context import Context
from pypyr.errors import (Call,
                          ContextError,
                          Jump,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.steps.dsl.cof import control_of_flow_instruction as cof_func

from tests.common.utils import patch_logger

# cof_func(name, instruction_type, context, context_key)


def test_cof_name_required():
    """A CoF requires name."""
    with pytest.raises(AssertionError):
        cof_func(None, None, None, None)


def test_cof_context_required():
    """A CoF requires context."""
    with pytest.raises(AssertionError):
        cof_func('blah', None, None, None)


def test_cof_context_key_required():
    """A CoF requires context_key in context."""
    with pytest.raises(KeyNotInContextError) as err:
        cof_func('blah', None, Context({'a': 'b'}), 'key')

    assert str(err.value) == ("context['key'] doesn't exist. It must exist "
                              "for blah.")


def test_cof_context_key_groups_required():
    """A CoF requires context_key groups in context."""
    with pytest.raises(KeyNotInContextError) as err:
        cof_func('blah', None, Context({'key': {'a': 'b'}}), 'key')

    assert str(err.value) == ("key needs a child key 'groups', which should "
                              "be a list or a str with the step-group name(s) "
                              "you want to run. This is for step blah.")


def test_cof_context_key_groups_wrong_type():
    """A CoF requires context_key groups in context of str or dict."""
    with pytest.raises(ContextError) as err:
        cof_func('blah', None, Context({'key': False}), 'key')

    assert str(err.value) == ("key needs a child key 'groups', which should "
                              "be a list or a str with the step-group name(s) "
                              "you want to run. This is for step blah. "
                              "Instead, you've got False")


def test_cof_context_key_exists_but_none():
    """A CoF requires context_key in context."""
    with pytest.raises(KeyInContextHasNoValueError) as err:
        cof_func('blah', None, Context({'key': {'groups': None}}), 'key')

    assert str(err.value) == ("key.groups must have a value for step blah")


def test_cof_str_input():
    """Simple str becomes wrapped in groups list."""
    with pytest.raises(Call) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=Context({'key': 'b'}),
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b']
    assert not cof.success_group
    assert not cof.failure_group
    assert cof.original_config == ('key', 'b')


def test_cof_list_input():
    """List becomes the groups list."""
    with pytest.raises(Call) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=Context({'key': ['b', 'c']}),
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b', 'c']
    assert not cof.success_group
    assert not cof.failure_group
    assert cof.original_config == ('key', ['b', 'c'])


def test_cof_mutating_original_config():
    """Original config abides even when context mutates."""
    input_list = ['b', 'c']
    context = Context({'key': input_list})
    with pytest.raises(Call) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=context,
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b', 'c']
    assert not cof.success_group
    assert not cof.failure_group

    # mutate the list instance
    input_list[0] = 'changed'
    assert context['key'][0] == 'changed'

    # new list instance creates new object, original remains intact
    input_list = ['d', 'e']
    assert context['key'][0] == 'changed'
    assert cof.original_config == ('key', ['changed', 'c'])


def test_cof_dict_with_str_input():
    """Dict with simple str becomes wrapped in groups list."""
    with pytest.raises(Call) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=Context({'key': {'groups': 'b'}}),
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b']
    assert not cof.success_group
    assert not cof.failure_group
    assert cof.original_config == ('key', {'groups': 'b'})


def test_cof_dict_with_list_input():
    """Dict with simple list."""
    with pytest.raises(Call) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=Context({'key': {'groups': ['b', 'c']}}),
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b', 'c']
    assert not cof.success_group
    assert not cof.failure_group
    assert cof.original_config == ('key', {'groups': ['b', 'c']})


def test_cof_dict_with_all_args():
    """Dict with all values set."""
    with pytest.raises(Call) as err:
        with patch_logger('blah', logging.INFO) as mock_logger_info:
            cof_func(name='blah',
                     instruction_type=Call,
                     context=Context({'key': {'groups': ['b', 'c'],
                                              'success': 'sg',
                                              'failure': 'fg'}}),
                     context_key='key')

    cof = err.value
    assert isinstance(cof, Call)
    assert cof.groups == ['b', 'c']
    assert cof.success_group == 'sg'
    assert cof.failure_group == 'fg'
    assert cof.original_config == ('key', {'groups': ['b', 'c'],
                                           'success': 'sg',
                                           'failure': 'fg'})

    mock_logger_info.assert_called_once_with(
        "step blah about to hand over control with key: Will run groups: "
        "['b', 'c']  with success sg and failure fg")


def test_cof_dict_with_success_not_a_string():
    """Dict with success_group not a string should raise."""
    with pytest.raises(ContextError) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=Context({'key': {'groups': ['b', 'c'],
                                          'success': 1,
                                          'failure': 'fg'}}),
                 context_key='key')

    assert str(err.value) == "key.success must be a string for blah."


def test_cof_dict_with_failure_not_a_string():
    """Dict with failure_group not a string should raise."""
    with pytest.raises(ContextError) as err:
        cof_func(name='blah',
                 instruction_type=Call,
                 context=Context({'key': {'groups': ['b', 'c'],
                                          'success': '1',
                                          'failure': False}}),
                 context_key='key')

    assert str(err.value) == "key.failure must be a string for blah."


def test_cof_dict_with_all_args_formatting():
    """Dict with all values set from formatting expressions."""
    with pytest.raises(Jump) as err:
        cof_func(name='blah',
                 instruction_type=Jump,
                 context=Context({
                     'list': ['b', 'c'],
                     'sg': 'sgv',
                     'fg': 'fgv',
                     'key': {
                         'groups': '{list}',
                         'success': '{sg}',
                         'failure': '{fg}'
                     }}),
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Jump)
    assert cof.groups == ['b', 'c']
    assert cof.success_group == 'sgv'
    assert cof.failure_group == 'fgv'
    assert cof.original_config == ('key', {'groups': '{list}',
                                           'success': '{sg}',
                                           'failure': '{fg}'
                                           })


def test_cof_dict_with_all_args_formatting_to_string():
    """Dict with all values set from formatting expressions to string."""
    with pytest.raises(Jump) as err:
        cof_func(name='blah',
                 instruction_type=Jump,
                 context=Context({
                     'list': 'abc',
                     'sg': 'sgv',
                     'fg': 'fgv',
                     'key': {
                         'groups': '{list}',
                         'success': '{sg}',
                         'failure': '{fg}'
                     }}),
                 context_key='key')

    cof = err.value
    assert isinstance(cof, Jump)
    assert cof.groups == ['abc']
    assert cof.success_group == 'sgv'
    assert cof.failure_group == 'fgv'
    assert cof.original_config == ('key', {'groups': '{list}',
                                           'success': '{sg}',
                                           'failure': '{fg}'
                                           })
