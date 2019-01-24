"""pathcheck.py integration tests."""
import logging
from unittest.mock import patch
from pypyr.context import Context
import pypyr.steps.pathcheck as pathchecker


def test_pathcheck_list_none():
    """Multiple paths ok with none returning match."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': ['./{ok1}/x', './arb/{ok1}', '{ok1}/arb/z']})

    logger = logging.getLogger('pypyr.steps.pathcheck')
    with patch.object(logger, 'info') as mock_logger_info:
        pathchecker.run_step(context)

    mock_logger_info.assert_called_once_with('checked 3 path(s) and found 0')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == ['./{ok1}/x', './arb/{ok1}', '{ok1}/arb/z']
    assert context["pathCheckOut"] == {
        './{ok1}/x': {
            'exists': False,
            'count': 0,
            'found': []
        },
        './arb/{ok1}': {
            'exists': False,
            'count': 0,
            'found': []
        },
        '{ok1}/arb/z': {
            'exists': False,
            'count': 0,
            'found': []
        },
    }


def test_pathcheck_single_with_formatting():
    """Single path ok with string formatting."""
    context = Context({
        'ok1': 'arb',
        'pathCheck': './tests/testfiles/glob/{ok1}.3'})

    pathchecker.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'arb'
    assert context['pathCheck'] == './tests/testfiles/glob/{ok1}.3'
    assert context["pathCheckOut"] == {'./tests/testfiles/glob/{ok1}.3': {
        'exists': True,
        'count': 1,
        'found': ['./tests/testfiles/glob/arb.3']
    }}


def test_pathcheck_list():
    """Multiple paths ok with some returning no match."""
    context = Context({
        'ok1': 'ov1',
        'pathCheck': ['./tests/testfiles/glob/arb.1',
                      './tests/testfiles/glob/arb.2*',
                      './tests/testfiles/glob/arb.XX']})

    logger = logging.getLogger('pypyr.steps.pathcheck')
    with patch.object(logger, 'info') as mock_logger_info:
        pathchecker.run_step(context)

    mock_logger_info.assert_called_once_with('checked 3 path(s) and found 3')

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 3 items"
    assert context['ok1'] == 'ov1'
    assert context['pathCheck'] == ['./tests/testfiles/glob/arb.1',
                                    './tests/testfiles/glob/arb.2*',
                                    './tests/testfiles/glob/arb.XX']

    assert len(context["pathCheckOut"]) == 3

    found = context["pathCheckOut"]['./tests/testfiles/glob/arb.1']
    assert found
    assert found['exists']
    assert found['count'] == 1
    assert found['found'] == ['./tests/testfiles/glob/arb.1']

    found = context["pathCheckOut"]['./tests/testfiles/glob/arb.2*']
    assert found
    assert found['exists']
    assert found['count'] == 2
    frozen_actual_found = frozenset(found['found'])
    frozen_expected_found = frozenset(['./tests/testfiles/glob/arb.2',
                                       './tests/testfiles/glob/arb.2.2'])

    assert frozen_actual_found == frozen_expected_found

    found = context["pathCheckOut"]['./tests/testfiles/glob/arb.XX']
    assert found
    assert not found['exists']
    assert found['count'] == 0
    assert found['found'] == []
