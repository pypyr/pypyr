"""All pipelines."""
from invoke import task

from . import MyTask, lint, test


@task(lint.all, test.all, klass=MyTask)
def buildout(c):
    """Lint and test."""
    pass
