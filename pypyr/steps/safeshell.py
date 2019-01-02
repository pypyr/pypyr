"""pypyr step that executes a cmd as a sub-process.

Alias for pypyr.steps.cmd

You cannot use things like exit, return, shell pipes, filename wildcards,
environment,variable expansion, and expansion of ~ to a user’s home
directory.
"""
import logging
import pypyr.steps.cmd

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Run command, program or executable.

    Context is a dictionary or dictionary-like.

    Context must contain the following keys:
    cmd: <<cmd string>> (command + args to execute.)

    OR, as a dict
    cmd:
        run: str. mandatory. <<cmd string>> command + args to execute.
        save: bool. defaults False. save output to cmdOut.

    Will execute the command string in the shell as a sub-process.
    Escape curly braces: if you want a literal curly brace, double it like
    {{ or }}.

    If save is True, will save the output to context as follows:
        cmdOut:
            returncode: 0
            stdout: 'stdout str here. None if empty.'
            stderr: 'stderr str here. None if empty.'

    cmdOut.returncode is the exit status of the called process. Typically 0
    means OK. A negative value -N indicates that the child was terminated by
    signal N (POSIX only).

    context['cmd'] will interpolate anything in curly braces for values
    found in context. So if your context looks like this:
        key1: value1
        key2: value2
        cmd: mything --arg1 {key1}

    The cmd passed to the shell will be "mything --arg value1"
    """
    logger.debug("started")

    pypyr.steps.cmd.run_step(context)

    logger.debug("done")
