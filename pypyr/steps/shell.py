"""pypyr step that executes a shell as a sub-process.

The command string must be formatted exactly as it would be when typed
at the shell prompt. This includes, for example, quoting or backslash escaping
filenames with spaces in them. The shell defaults to /bin/sh.
"""
import logging
from pypyr.steps.dsl.cmd import CmdStep

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Run shell command without shell interpolation.

    Context is a dictionary or dictionary-like.

    Context must contain the following keys:
    cmd: <<cmd string>> (command + args to execute.)

    OR, as a dict
    cmd:
        run: str. mandatory. <<cmd string>> command + args to execute.
        save: bool. defaults False. save output to cmdOut.

    Will execute command string in the shell as a sub-process.
    The shell defaults to /bin/sh.
    The context['cmd'] string must be formatted exactly as it would be when
    typed at the shell prompt. This includes, for example, quoting or backslash
    escaping filenames with spaces in them.
    There is an exception to this: Escape curly braces: if you want a literal
    curly brace, double it like {{ or }}.

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

    CmdStep(name=__name__, context=context, is_shell=True).run_step()

    logger.debug("done")
