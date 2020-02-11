"""Pytest configuration file.

This is a bit of a, ahem, alternative way of allowing testpy to find the pypyr
module, without having to go into your virtualenv or dealing with setup.py
first. This is because pytest makes the dir this file is in the root.

What this file is actually for is per-directory fixture scopes:
http://doc.pytest.org/en/latest/example/simple.html#package-directory-level-fixtures-setups
"""
import logging

from pypyr.log.logger import set_root_logger, set_up_notify_log_level

set_up_notify_log_level()
set_root_logger(logging.DEBUG)
