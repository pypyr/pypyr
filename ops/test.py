"""Tests (all sorts of).

Used as invoke namespace module.
"""
from invoke.tasks import call, task

from . import MyTask, config


@task(config.all, klass=MyTask)
def test_to_terminal(c):
    """tests, output to terminal with line nos.

    test & coverage
    """
    cfg = c.config
    cmd = (
        f"pytest --cov={cfg.package_name} "
        f"--cov-report term-missing:skip-covered "
        f" {cfg.test_dir}"
    )
    c.run(cmd)


@task(config.all, klass=MyTask)
def test_to_file(c):
    """tests, output to file.

    test & coverage but with file output
    """
    cfg = c.config
    print(f"output_coverage: {cfg.output_coverage}")
    cmd = (
        f"pytest --cov={cfg.package_name} "
        f"--cov-report term-missing "
        f"--cov-report {cfg.output_coverage} "
        f"--junitxml={cfg.output_test_results}"
        f"{cfg.test_dir}"
    )
    c.run(cmd)


@task(klass=MyTask)
def codecov(c):
    """Coverage (possibly with result upload).

    Coverage upload only works like this on CI.

    If you want to run local you need to give -t upload-token switch.
    """
    c.run("codecov")


@task(config.all, klass=MyTask)
def all(c):
    """Run all CI/CD either in local or remote (CI/CD server) mode.

    CI/CD mode is detected by env var CI being true.
    """
    if c.config.is_ci:
        call(test_to_file).task(c)
        call(codecov).task(c)
    else:
        call(test_to_terminal).task(c)
