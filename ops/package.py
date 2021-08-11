"""Build packages."""
from invoke import task, call


@task
def build_dist(c):
    """Build wheel + sdist to dist/."""
    c.run("python setup.py bdist_wheel sdist")


@task
def verify_long_description(c):
    """verify/check new package in dist/.

    verify README/long_description
    """
    c.run("twine check dist/*")


@task
def all(c):
    """Run all package build tasks."""
    call(build_dist).task(c)
    call(verify_long_description).task(c)
