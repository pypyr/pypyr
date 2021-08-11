"""Bumping package version."""
from invoke import call, task

from . import MyTask, config, pipeline_buildout, step


@task(
    pipeline_buildout.buildout,
    klass=MyTask,
    help={
        "bump_size": (
            "Part of version to bump. "
            "One of [major, minor, patch]. "
            "Default: patch"
        )
    },
)
def bumpversion(c, bump_size="patch"):
    """Bump the package version."""
    step("bump_size expects major, minor or patch")
    assert bump_size in ["major", "minor", "patch"]

    step("bumping version")
    c.run(f"bumpversion --no-tag  --commit {bump_size}")

    step("report new version")
    call(config.show_version).task(c)


@task(klass=MyTask)
def git_push(c):
    """Push the new version up (git)."""
    c.run("git push")
