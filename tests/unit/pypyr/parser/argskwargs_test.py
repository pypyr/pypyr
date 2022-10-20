"""Unit tests for pypyr.parser.argskwargs."""

from pypyr.parser.argskwargs import get_parsed_context


def test_argskwargs_empty_input():
    """Parse empty inputs."""
    assert get_parsed_context([]) == {'argList': []}
    assert get_parsed_context(None) == {'argList': []}


def test_argskwargs_args_only():
    """Parse when only args."""
    assert get_parsed_context(['a']) == {'argList': ['a']}
    assert get_parsed_context(['a', 'b b', 'c']) == {'argList':
                                                     ['a', 'b b', 'c']}


def test_argskwargs_kwargs_only():
    """Parse when only kwargs."""
    assert get_parsed_context(['k1=value 1']) == {'argList': [],
                                                  'k1': 'value 1'}
    assert get_parsed_context(['k1=value 1', 'k2=v2=3']) == {'argList': [],
                                                             'k1': 'value 1',
                                                             'k2': 'v2=3'}


def test_argskwargs_args_and_kwargs():
    """Parse when args + kwargs."""
    assert get_parsed_context(['a', 'b', 'c d',
                               'k1="value 1"', 'k2=v2']) == {
        'argList': ['a', 'b', 'c d'],
        'k1': '"value 1"',
        'k2': 'v2'}
