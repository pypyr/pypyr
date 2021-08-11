"""Lint code and package metadata."""
from invoke import task


@task
def setup_meta(c):
    """Verify setup.py metadata.

    This will soon (?) deprecate in favor of twine --check.
    For the moment twine still only checks README validity, and not
    metadata.
    """
    c.run("python setup.py check -m -s")


@task
def flake8(c):
    """flake8 linting."""
    c.run("flake8")


@task(pre=[setup_meta, flake8])
def all(c):
    """Run all lint tasks."""
    pass
