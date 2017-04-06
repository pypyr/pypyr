"""pypyr Step that executes a safe shell as a sub-process.

You cannot use things like exit, return, shell pipes, filename wildcards,
environment,variable expansion, and expansion of ~ to a user’s home
directory.
"""
import pypyr.log.logger
import subprocess

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Run shell command without shell interpolation.

    Context is a dictionary or dictionary-like.
    Will execute context['cmd'] in the shell as a sub-process.

    context is mandatory. When you execute the pipeline, it should look
    something like this: pipeline-runner [name here] --context 'cmd=ls -a'.
    """
    logger.debug("started")
    assert context, ("context must be set for step shell. Did you set "
                     "--context 'cmd=<<shell cmd here>>'?")
    assert 'cmd' in context, ("context['cmd'] must exist for step shell.")

    # input string is a command like 'ls -l | grep boom'. Split into list on
    # spaces to allow for natural shell language input string.
    logger.debug(f"Executing command string: {context['cmd']}")
    args = context['cmd'].split(' ')
    logger.debug(f"Prepared command sequence: {args}")

    # check=True throws CalledProcessError if exit code != 0
    subprocess.run(args, shell=False, check=True)

    logger.debug("done")
    return context
