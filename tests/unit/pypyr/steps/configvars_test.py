"""configvars.py unit tests."""
from pypyr.context import Context
from pypyr.steps import configvars


def test_configvars_empty_vars():
    """Do nothing when config.vars is empty."""
    context = Context()
    configvars.run_step(context)
    assert context == {}


def test_configvars_with_vars_to_empty_context(monkeypatch):
    """Copy to empty context when config.vars has values."""
    monkeypatch.setattr('pypyr.config.config.vars', {'a': 'b', 'c': 'd'})

    context = Context()
    configvars.run_step(context)
    assert context == {'a': 'b', 'c': 'd'}


def test_configvars_with_vars_to_context(monkeypatch):
    """Copy to existing context when config.vars has values."""
    monkeypatch.setattr('pypyr.config.config.vars', {'a': 'b', 'c': 'd'})

    context = Context({'og': 1, 'og2': 'v2'})
    configvars.run_step(context)
    assert context == {'og': 1, 'og2': 'v2', 'a': 'b', 'c': 'd'}
