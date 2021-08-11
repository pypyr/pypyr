"""Internal tasks managing configuration.

Intended as pre-tasks.

"""
import os

from invoke import task

from . import MyTask


@task(klass=MyTask)
def all(c):
    """Complete and validate needed cfg.

    Modifies `c.config` by adding needed values.

    May perform some validation.

    Must be set as @task(configure]) on relevant task to take effect.
    """
    cfg = c.config
    expected_keys = ["package_name", "version_module_name", "output_results_dir"]
    for key in expected_keys:
        assert key in cfg, f"key {key} shall exist in config"
    cfg.output_coverage = f"xml:{cfg.output_results_dir}/codecoverage/coverage.xml"
    cfg.output_test_results = f"{cfg.output_results_dir}/testresults/junitresults.xml"
    is_ci = bool(os.environ.get("CI", False))
    cfg.is_ci = is_ci
