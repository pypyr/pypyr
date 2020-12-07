"""contextclearall.py unit tests."""
import builtins

from pypyr.context import Context
import pypyr.steps.contextclearall


def test_context_clear_all_pass():
    """Context Clear All removes everything from context."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4',
        'contextClear': [
            'key2',
            'key4',
            'contextClear'
        ]
    })

    # len is only the one added item 'a'
    assert context.pystring_globals_update({'a': 'b'}) == 1

    pypyr.steps.contextclearall.run_step(context)

    assert len(context) == 0
    assert context is not None
    assert isinstance(context, Context)

    assert type(context._pystring_globals) is dict
    assert context._pystring_globals == {}
    assert list(dict.items(context._pystring_namespace)) == [
        ('__builtins__', builtins.__dict__)]

    assert context._pystring_namespace.maps == [{}, {}]

    context['k1'] = 'value1'

    assert context['k1'] == 'value1'
    # global namespace still works.
    assert context.get_eval_string('len(k1)') == 6


def test_context_clear_all_context_empty_already():
    """Context Clear All removes everything from context from empty."""
    context = Context()

    pypyr.steps.contextclearall.run_step(context)

    assert len(context) == 0
    assert len(context._pystring_globals) == 0
    assert context._pystring_globals == {}
