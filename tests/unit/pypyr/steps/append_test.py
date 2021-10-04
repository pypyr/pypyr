"""append.py unit tests."""
import pytest

from pypyr.context import Context
from pypyr.dsl import PyString
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.steps import append


# region validation
def test_append_no_input():
    """Context append must exist."""
    with pytest.raises(KeyNotInContextError):
        append.run_step(Context())


def test_append_not_a_dict():
    """Context append must be a dict."""
    with pytest.raises(ContextError) as err:
        append.run_step(Context({
            'append': 1}))

    assert str(err.value) == (
        "context['append'] must exist, be iterable and contain 'list' for "
        "pypyr.steps.append. argument of type 'int' is not iterable")


def test_append_no_base_object():
    """List input must exist."""
    with pytest.raises(KeyNotInContextError) as err:
        append.run_step(Context({
            'append': {}}))

    assert str(err.value) == (
        "context['append']['list'] doesn't exist. It must exist for "
        "pypyr.steps.append.")


def test_append_no_add_me():
    """Input add_me must exist."""
    with pytest.raises(KeyNotInContextError):
        append.run_step(Context({
            'append': {
                'list': 'arblist'
            }}))


def test_append_with_empty_base():
    """Input list is empty."""
    with pytest.raises(KeyInContextHasNoValueError):
        append.run_step(Context({
            'append': {
                        'list': '',
                        'addMe': ''}}))


def test_append_with_none_base():
    """Input list is empty."""
    with pytest.raises(KeyInContextHasNoValueError):
        append.run_step(Context({
            'append': {
                        'list': None,
                        'addMe': None}}))


# endregion validation

def test_append_with_none_add():
    """Add None to list."""
    context = Context({
        'append': {
            'list': 'arblist',
            'addMe': None
        }})

    append.run_step(context)

    context['append']['addMe'] = 'one'

    append.run_step(context)

    assert context['arblist'] == [None, 'one']
    assert len(context) == 2


def test_append_pass_with_minimal_create():
    """Create list with minimal parameters success."""
    context = Context({
        'append': {
            'list': 'arblist',
            'addMe': 1
        }})

    append.run_step(context)

    context['append']['addMe'] = 2

    append.run_step(context)

    assert context['arblist'] == [1, 2]
    assert len(context) == 2


def test_append_pass_with_create_from_list_no_extend():
    """Minimal paramaters success."""
    context = Context({
        'append': {
            'list': 'arblist',
            'addMe': [1, 2]
        }})

    append.run_step(context)

    context['append']['addMe'] = 3

    append.run_step(context)

    assert context['arblist'] == [[1, 2], 3]
    assert len(context) == 2


def test_append_pass_with_create_from_list_extend():
    """Create new list with extend."""
    context = Context({
        'append': {
            'list': 'arblist',
            'addMe': [1, 2],
            'unpack': True
        }})

    append.run_step(context)

    context['append']['unpack'] = False
    context['append']['addMe'] = 3

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3]
    assert len(context) == 2


def test_append_pass_existing():
    """Append existing list."""
    context = Context({
        'arblist': [1, 2],
        'append': {
            'list': 'arblist',
            'addMe': 3
        }})

    append.run_step(context)

    context['append']['addMe'] = 4

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3, 4]
    assert len(context) == 2


def test_append_pass_with_extend_existing():
    """Extend existing list."""
    context = Context({
        'arblist': [1, 2],
        'append': {
            'list': 'arblist',
            'addMe': [3, 4],
            'unpack': True
        }})

    append.run_step(context)

    context['append']['unpack'] = False
    context['append']['addMe'] = 5

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3, 4, 5]
    assert len(context) == 2


def test_append_with_list_input():
    """Input is a list, not a string key."""
    context = Context({
        'arblist': [1, 2],
        'append': {
            'list': PyString('arblist'),
            'addMe': 3
        }})

    append.run_step(context)

    context['append']['addMe'] = 4

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3, 4]
    assert len(context) == 2


def test_append_with_list_input_extend():
    """Input is a list, not a string key with an extend."""
    context = Context({
        'arblist': [1, 2],
        'append': {
            'list': PyString('arblist'),
            'addMe': 3
        }})

    append.run_step(context)

    context['append']['addMe'] = [4, 5]
    context['append']['unpack'] = True

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3, 4, 5]
    assert len(context) == 2


def test_append_with_formatting():
    """Use formatting expressions."""
    context = Context({
        'arblist': [1, 2],
        'addthis': 3,
        'append': {
            'list': PyString('arblist'),
            'addMe': '{addthis}'
        }})

    append.run_step(context)

    context['append']['addMe'] = 4

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3, 4]
    assert len(context) == 3


def test_append_list_with_formatting_no_extend():
    """Use formatting expressions to append list without extend."""
    context = Context({
        'arblist': [1, 2],
        'addthis': [3, 4],
        'append': {
            'list': PyString('arblist'),
            'addMe': '{addthis}'
        }})

    append.run_step(context)

    context['append']['addMe'] = 5

    append.run_step(context)

    assert context['arblist'] == [1, 2, [3, 4], 5]
    assert len(context) == 3


def test_append_with_formatting_extend():
    """Use formatting expressions."""
    context = Context({
        'arblist': [1, 2],
        'addthis': [3, 4],
        'extend_me': True,
        'append': {
            'list': PyString('arblist'),
            'addMe': '{addthis}',
            'unpack': '{extend_me}'
        }})

    append.run_step(context)

    context['append']['addMe'] = [5, 6]

    append.run_step(context)

    assert context['arblist'] == [1, 2, 3, 4, 5, 6]
    assert len(context) == 4


def test_append_with_strings():
    """Append strings."""
    context = Context({
        'arblist': [1, 2],
        'append': {
            'list': PyString('arblist'),
            'addMe': 'three'
        }})

    append.run_step(context)

    context['append']['addMe'] = 'four'

    append.run_step(context)

    assert context['arblist'] == [1, 2, 'three', 'four']
    assert len(context) == 2


def test_append_with_strings_unpack():
    """Append strings with unpack."""
    context = Context({
        'arblist': [1, 2],
        'append': {
            'list': PyString('arblist'),
            'addMe': 'xy',
            'unpack': True
        }})

    append.run_step(context)

    context['append']['addMe'] = 'z'

    append.run_step(context)

    assert context['arblist'] == [1, 2, 'x', 'y', 'z']
    assert len(context) == 2
