"""Bump version and git push."""
from invoke import call, task

from . import MyTask, bump


@task(klass=MyTask)
def pipeline_bump(c, bump_size=None):
    """Bump the version and git push."""
    c.config.bump_size = bump_size
    call(bump.bumpversion, bump_size=bump_size).task(c)
    call(bump.git_push)
