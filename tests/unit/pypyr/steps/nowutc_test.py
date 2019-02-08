"""nowutc.py unit tests."""
from datetime import datetime, timezone
from unittest.mock import patch, Mock
from pypyr.context import Context
import pypyr.steps.nowutc as nowutc_step

frozen_timestamp = datetime.now(timezone.utc)


@patch('pypyr.steps.nowutc.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_nowutc_default_iso():
    """Now gets date in iso format."""
    context = Context()
    nowutc_step.run_step(context)

    assert context['nowUtc'] == frozen_timestamp.isoformat()


@patch('pypyr.steps.nowutc.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_nowutc_with_formatting_date_part():
    """Now gets timestamp with formatting."""
    context = Context({'nowUtcIn': '%Y%m%d'})
    nowutc_step.run_step(context)

    assert context['nowUtc'] == frozen_timestamp.strftime('%Y%m%d')


@patch('pypyr.steps.nowutc.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_nowutc_with_formatting_time_part():
    """Now gets timestamp with date formatting."""
    context = Context({'nowUtcIn': '%I hour %M %p blah %Z'})
    nowutc_step.run_step(context)

    assert context['nowUtc'] == frozen_timestamp.strftime(
        '%I hour %M %p blah UTC')


@patch('pypyr.steps.nowutc.datetime',
       Mock(now=Mock(return_value=frozen_timestamp)))
def test_nowutc_with_formatting_interpolation():
    """Now gets timestamp with date formatting and pypyr interpolation."""
    context = Context({'f': '%Y %w', 'nowUtcIn': '%A {f}'})
    nowutc_step.run_step(context)

    assert context['nowUtc'] == frozen_timestamp.strftime('%A %Y %w')
