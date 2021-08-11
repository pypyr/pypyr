"""Publish built packages.

Packages have to be already built and existing in dist directory.

To publish to private repo, use env vars::

    export TWINE_REPOSITORY_URL=http://10.0.0.1:3141/javl/dev
    export TWINE_USERNAME=javl
    export TWINE_PASSWORD=realpassword
    export PIP_INDEX_URL=$TWINE_REPOSITORY_URL

Alternatively, use TWINE_REPOSITORY (name of section in .pypirc) + configure
relevant PIP_INDEX_URL.
"""
import time

from invoke import task

from . import step


def get_version(version_module_name):
    """Load currently declared package version."""
    import importlib

    version_module = importlib.import_module(version_module_name)
    # always reload
    importlib.reload(version_module)

    version = f"{version_module.__version__}"
    print(f"version is {version}")
    return version


@task
def all(c):
    """Publish built packages to (public or private) pypi."""
    cfg = c.config

    step("check intended package version")
    version = get_version(cfg.version_module_name)

    step("publishing package to pypi")
    c.run(f"twine upload dist/{cfg.package_name}-{version}*")

    step(
        "uninstall current version of package before attempting to reinstall from pypi"
    )
    c.run(f"pip uninstall -y {cfg.package_name}")

    step("set expected version")
    expected_version = version

    step("giving pypi 10s before testing release")
    time.sleep(10)

    step("installing just published release from pypi for smoke-test")
    max_tries = 5
    sleep_time = 10
    i = 1
    cmd = f"pip install --upgrade --no-cache-dir {cfg.package_name}=={expected_version}"
    while True:  # retry few times if problems
        res = c.run(
            cmd, warn=i < max_tries
        )  # first runs tollerate failure, last one not
        if res.ok:
            break
        time.sleep(sleep_time)

    step("update version from newly installed package")
    version = get_version(cfg.version_module_name)

    step("checking published package version as expected")
    assert version == expected_version

    step("reset the tox cache.")

    # at this point, tox contains the pip compiled pypyr, rather than the -e
    # dev install.  currently CI not smart enough to save changes to cache, but
    # this could well change, so prevent future problems.  When running locally
    # failing to do this will lead to surprises of not running local
    # verification against the actual latest local.
    c.run("pip install -e .")
