"""Build packages."""
from invoke import task

from . import MyTask, step


@task(klass=MyTask)
def all(c):
    """Run all package build tasks."""
    step("Build wheel + sdist to dist/.")
    c.run("python setup.py bdist_wheel sdist")

    step("verify/check new package in dist/")
    # verify README/long_description
    c.run("twine check --strict dist/*")
