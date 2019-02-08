"""now.py unit tests."""
from datetime import datetime
from dateutil.tz import tzlocal
from unittest.mock import patch, Mock
from pypyr.context import Context
import pypyr.steps.now as now_step

frozen_timestamp = datetime.now(tzlocal())


@patch('pypyr.steps.now.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_now_default_iso():
    """Now gets date in iso format."""
    context = Context()
    now_step.run_step(context)

    assert context['now'] == frozen_timestamp.isoformat()


@patch('pypyr.steps.now.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_now_with_formatting_date_part():
    """Now gets timestamp with formatting."""
    context = Context({'nowIn': '%Y%m%d'})
    now_step.run_step(context)

    assert context['now'] == frozen_timestamp.strftime('%Y%m%d')


@patch('pypyr.steps.now.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_now_with_formatting_time_part():
    """Now gets timestamp with formatting."""
    context = Context({'nowIn': '%I hour %M %p blah %Z'})
    now_step.run_step(context)

    assert context['now'] == frozen_timestamp.strftime(
        '%I hour %M %p blah %Z')


@patch('pypyr.steps.now.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_now_with_formatting_interpolation():
    """Now gets timestamp with date formatting and pypyr interpolation."""
    context = Context({'f': '%Y %w', 'nowIn': '%A {f}'})
    now_step.run_step(context)

    assert context['now'] == frozen_timestamp.strftime('%A %Y %w')
