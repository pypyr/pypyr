"""Internal tasks managing configuration.

Intended as pre-tasks.

"""
import os

from invoke import task


@task
def all(c):
    """Complete and validate needed cfg.

    Modifies `c.config` by adding needed values.

    May perform some validation.

    Must be set as @task(pre=[configure]) on relevant task to take effect.
    """
    cfg = c.config
    expected_keys = ["package_name", "version_module_name", "output_results_dir"]
    for key in expected_keys:
        assert key in cfg, f"key {key} shall exist in config"
    cfg.output_coverage = f"xml:{cfg.output_results_dir}/codecoverage/coverage.xml"
    cfg.output_test_results = f"{cfg.output_results_dir}/testresults/junitresults.xml"
    is_ci = bool(os.environ.get("CI", False))
    cfg.is_ci = is_ci


@task
def version(c):
    """Load currently declared package version."""
    import importlib

    cfg = c.config

    version_module = importlib.import_module(c.config.version_module_name)
    if "is_version_module_loaded" in cfg:
        importlib.reload(version_module)

    cfg.version = f"{version_module.__version__}"
    cfg.is_version_module_loaded = True
    print(f"version is {c.config.version}")
