"""Pytest configuration file.

This is a bit of a, ahem, alternative way of allowing testpy to find the pypyr
module, without having to go into your virtualenv or dealing with pip install
first. This is because pytest makes the dir this file is in the root & adds it
to sys.paths for you.

If you remove this file, pytest will fail UNLESS you `pip install -e .[dev]`.

Keeping this file means you can run pytest in an environment with all the
other dependencies installed but not pypyr itself.

What this file is actually for is per-directory fixture scopes:
http://doc.pytest.org/en/latest/example/simple.html#package-directory-level-fixtures-setups
"""
