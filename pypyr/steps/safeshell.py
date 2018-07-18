"""pypyr Step that executes a safe shell as a sub-process.

You cannot use things like exit, return, shell pipes, filename wildcards,
environment,variable expansion, and expansion of ~ to a user’s home
directory.
"""
import logging
import subprocess

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Run shell command without shell interpolation.

    Context is a dictionary or dictionary-like.
    Will execute context['cmd'] in the shell as a sub-process.
    Escape curly braces: if you want a literal curly brace, double it like
    {{ or }}.

    context is mandatory. When you execute the pipeline, it should look
    something like this: pipeline-runner [name here] 'cmd=ls -a'.

    context['cmd'] will interpolate anything in curly braces for values
    found in context. So if your context looks like this:
        key1: value1
        key2: value2
        cmd: mything --arg1 {key1}

    The cmd passed to the shell will be "mything --arg value1"
    """
    logger.debug("started")
    context.assert_key_has_value(key='cmd', caller=__name__)

    logger.debug(f"Processing command string: {context['cmd']}")
    interpolated_string = context.get_formatted('cmd')

    # input string is a command like 'ls -l | grep boom'. Split into list on
    # spaces to allow for natural shell language input string.
    args = interpolated_string.split(' ')

    # check=True throws CalledProcessError if exit code != 0
    subprocess.run(args, shell=False, check=True)

    logger.debug("done")
