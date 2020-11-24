"""contextclearall.py unit tests."""
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

    context.pystring_globals.update({'a': 'b'})

    pypyr.steps.contextclearall.run_step(context)

    assert len(context) == 0
    assert context is not None
    assert isinstance(context, Context)

    assert len(context.pystring_globals) == 0
    assert context.pystring_globals is not None
    assert type(context.pystring_globals) is dict

    context['k1'] = 'value1'

    assert context['k1'] == 'value1'


def test_context_clear_all_context_empty_already():
    """Context Clear All removes everything from context from empty."""
    context = Context()

    pypyr.steps.contextclearall.run_step(context)

    assert len(context) == 0
    assert len(context.pystring_globals) == 0
