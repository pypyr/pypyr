"""Lint code and package metadata."""
from invoke import call, task

from . import MyTask


@task(klass=MyTask)
def setup_meta(c):
    """Verify setup.py metadata.

    This will soon (?) deprecate in favor of twine --check.
    For the moment twine still only checks README validity, and not
    metadata.
    """
    c.run("python setup.py check -m -s")


@task(klass=MyTask)
def flake8(c):
    """flake8 linting."""
    c.run("flake8")


@task(klass=MyTask)
def all(c):
    """Run all lint tasks."""
    call(setup_meta).task(c)
    call(flake8).task(c)
