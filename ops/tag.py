"""Tag."""
from invoke import call, task

from . import MyTask, config, get_version, step


@task(klass=MyTask)
def set_git_config(c):
    """Set git user.name and user.email for github-actions.

    Meant to be run GitHub actions server, do not run locally.
    """
    step("setting git user.name")
    c.run("git config user.name github-actions")
    step("setting git user.email")
    c.run("git config user.email github-actions@github.com")


@task(config.all, klass=MyTask)
def tag(c):
    """Tag the commit on GitHub actions server."""
    cfg = c.config

    step("get current version")
    version = get_version(cfg.version_module_name)

    step("make sure local branch has latest tags from origin if local dev.")
    if cfg.is_ci:
        print("skipping as this step is not relevant on GitHub actions server.")
    else:
        c.run("git pull --tags")
        res = c.run(f'git tag -l "v{version}"')
        if res.stdout == f"v{version}":
            step("skipping rest of task as the tag already exist.")
            return

    step("create new tag for release")
    c.run(f'git tag "v{version}"')

    if cfg.is_ci:
        call(set_git_config).task(c)
