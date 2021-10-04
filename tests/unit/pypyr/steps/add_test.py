"""add.py unit tests."""
import pytest

from pypyr.context import Context
from pypyr.dsl import PyString
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
from pypyr.steps import add


# region validation
def test_add_no_input():
    """Context add must exist."""
    with pytest.raises(KeyNotInContextError):
        add.run_step(Context())


def test_add_not_a_dict():
    """Context add must be a dict."""
    with pytest.raises(ContextError) as err:
        add.run_step(Context({
            'add': 1}))

    assert str(err.value) == (
        "context['add'] must exist, be iterable and contain 'set' for "
        "pypyr.steps.add. argument of type 'int' is not iterable")


def test_add_no_base_object():
    """Set input must exist."""
    with pytest.raises(KeyNotInContextError) as err:
        add.run_step(Context({
            'add': {}}))

    assert str(err.value) == (
        "context['add']['set'] doesn't exist. It must exist for "
        "pypyr.steps.add.")


def test_add_no_add_me():
    """Input add_me must exist."""
    with pytest.raises(KeyNotInContextError):
        add.run_step(Context({
            'add': {
                'set': 'arbset'
            }}))


def test_add_with_empty_base():
    """Input list is empty."""
    with pytest.raises(KeyInContextHasNoValueError):
        add.run_step(Context({
            'add': {
                'set': '',
                'addMe': ''}}))


def test_add_with_none_base():
    """Input set is empty."""
    with pytest.raises(KeyInContextHasNoValueError):
        add.run_step(Context({
            'add': {
                'set': None,
                'addMe': None}}))


# endregion validation

def test_add_with_none_add():
    """Add None to set."""
    context = Context({
        'add': {
            'set': 'arbset',
            'addMe': None
        }})

    add.run_step(context)

    context['add']['addMe'] = 'one'

    add.run_step(context)

    assert context['arbset'] == {None, 'one'}
    assert len(context) == 2


def test_add_pass_with_minimal_create():
    """Create set with minimal parameters success."""
    context = Context({
        'add': {
            'set': 'arbset',
            'addMe': 1
        }})

    add.run_step(context)

    context['add']['addMe'] = 2

    add.run_step(context)

    assert context['arbset'] == {1, 2}
    assert len(context) == 2


def test_add_fail_with_create_from_list_unpack_implicit():
    """When addMe not hashable fail unless is list - unpack implicit True."""
    context = Context({
        'add': {
            'set': 'arbset',
            'addMe': [1, 2]
        }})

    add.run_step(context)

    context['add']['addMe'] = [3, 4]
    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4}
    assert len(context) == 2


def test_add_fail_with_create_from_list_unpack_false():
    """When addMe not hashable fail unless is list - unpack explicit False."""
    context = Context({
        'add': {
            'set': 'arbset',
            'addMe': [1, 2],
            'unpack': False
        }})

    with pytest.raises(TypeError):
        add.run_step(context)


def test_add_pass_with_create_from_list_extend():
    """Create new set with extend."""
    context = Context({
        'add': {
            'set': 'arbset',
            'addMe': [1, 2],
            'unpack': True
        }})

    add.run_step(context)

    context['add']['unpack'] = False
    context['add']['addMe'] = 3

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3}
    assert len(context) == 2


def test_add_pass_with_create_from_list_and_add():
    """Add lists with unpack explicitly true."""
    context = Context({
        'add': {
            'set': 'arbset',
            'addMe': [1, 2],
            'unpack': True
        }})

    add.run_step(context)

    context['add']['addMe'] = [3, 4]

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4}
    assert len(context) == 2


def test_add_pass_existing():
    """Add to existing set."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': 'arbset',
            'addMe': 3
        }})

    add.run_step(context)

    context['add']['addMe'] = 4

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4}
    assert len(context) == 2


def test_add_pass_with_extend_existing():
    """Extend existing set."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': 'arbset',
            'addMe': [3, 4],
            'unpack': True
        }})

    add.run_step(context)

    context['add']['unpack'] = False
    context['add']['addMe'] = 5

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4, 5}
    assert len(context) == 2


def test_add_with_set_input():
    """Input is a set, not a string key."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': PyString('arbset'),
            'addMe': 3
        }})

    add.run_step(context)

    context['add']['addMe'] = 4

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4}
    assert len(context) == 2


def test_add_with_set_input_extend():
    """Input is a set, not a string key with an extend."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': PyString('arbset'),
            'addMe': 3
        }})

    add.run_step(context)

    context['add']['addMe'] = [4, 5]
    context['add']['unpack'] = True

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4, 5}
    assert len(context) == 2


def test_add_with_formatting():
    """Use formatting expressions."""
    context = Context({
        'arbset': {1, 2},
        'addthis': 3,
        'add': {
            'set': PyString('arbset'),
            'addMe': '{addthis}'
        }})

    add.run_step(context)

    context['add']['addMe'] = 4

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4}
    assert len(context) == 3


def test_add_set_with_formatting_tuple():
    """Use formatting expressions to add tuple."""
    context = Context({
        'arbset': {1, 2},
        'addthis': (3, 4),
        'add': {
            'set': PyString('arbset'),
            'addMe': '{addthis}',
            'unpack': True
        }})

    add.run_step(context)

    context['add']['addMe'] = 5
    context['add']['unpack'] = False

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4, 5}
    assert len(context) == 3


def test_add_with_formatting_extend():
    """Use formatting expressions."""
    context = Context({
        'arbset': {1, 2},
        'addthis': [3, 4],
        'extend_me': True,
        'add': {
            'set': PyString('arbset'),
            'addMe': '{addthis}',
            'unpack': '{extend_me}'
        }})

    add.run_step(context)

    context['add']['addMe'] = [5, 6]

    add.run_step(context)

    assert context['arbset'] == {1, 2, 3, 4, 5, 6}
    assert len(context) == 4


def test_add_with_single_string():
    """Add single string."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': PyString('arbset'),
            'addMe': 'three'
        }})

    add.run_step(context)

    context['add']['addMe'] = 'four'

    add.run_step(context)

    assert context['arbset'] == {1, 2, 'three', 'four'}
    assert len(context) == 2


def test_add_with_strings():
    """Add multiple strings."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': PyString('arbset'),
            'addMe': ('three', 'four'),
            'unpack': True
        }})

    add.run_step(context)

    context['add']['unpack'] = False
    context['add']['addMe'] = 'five'

    add.run_step(context)

    assert context['arbset'] == {1, 2, 'three', 'four', 'five'}
    assert len(context) == 2


def test_add_with_strings_update():
    """Add strings with update."""
    context = Context({
        'arbset': {1, 2},
        'add': {
            'set': PyString('arbset'),
            'addMe': 'xy',
            'unpack': True
        }})

    add.run_step(context)

    context['add']['unpack'] = False
    context['add']['addMe'] = 'z'

    add.run_step(context)

    assert context['arbset'] == {1, 2, 'x', 'y', 'z'}
    assert len(context) == 2
