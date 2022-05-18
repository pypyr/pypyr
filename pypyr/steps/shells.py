"""pypyr step that executes commands in the shell as a sub-process.

The command string must be formatted exactly as it would be when typed
at the shell prompt. This includes, for example, quoting or backslash escaping
filenames with spaces in them. The shell defaults to /bin/sh on posix.
"""
import logging
from pypyr.steps.dsl.cmdasync import AsyncCmdStep

logger = logging.getLogger(__name__)


def run_step(context):
    """Run commands, programs or executables asynchronously, in parallel.

    Spawns a shell for each runnable item.

    Context is a pypyr.context.Context. This is dict-like.

    Context must contain the following keys:
        cmds:
            - <<shell string 1>>
            - <<shell string 2>>

    where <<cmd string>> is command + args to execute.

    You can alternatively use the expanded syntax to override default options:

    cmds:
        run: list[str | list[str]]. mandatory. command + args to execute.
            If list entry is another list[str], the sub-list will run in
            serial.
        save: bool. defaults False. save output to cmdOut. Treats output
            as text in the system's encoding and removes newlines at end.
        cwd: str/Pathlike. optional. Working directory for these commands.
        bytes (bool): Default False. When `save` return output bytes from
            cmds unaltered, without applying any encoding & text newline
            processing.
        encoding (str): Default None. When `save`, decode output with
            this encoding. The default of None uses the system encoding and
            should "just work".
        stdout (str | Path): Default None. Write stdout to this file path.
            Special value `/dev/null` writes to the system null device.
        stderr (str | Path): Default None. Write stderr to this file path.
            Special value `/dev/null` writes to the system null device.
            Special value `/dev/stdout` redirects err output to stdout.
        append (bool): Default False. When stdout/stderr a file, append
            rather than overwrite. Default is to overwrite.

    In expanded syntax, `run` can be a simple string or a list:
        cmds:
          run:
            - ./my-executable --arg
            - ./another-executable --arg
          save: False
          cwd: ./path/here

    Will execute the command string in the shell as a sub-process.
    Escape curly braces: if you want a literal curly brace, double it like
    {{ or }}.

    If save is True, will save the output as a list of results in the order
    executed. Each result is a pypyr.subproc.SubprocessResult, with the schema:
    cmd: the cmd/args executed
    returncode: 0
    stdout: 'stdout str here. None if empty.'
    stderr: 'stderr str here. None if empty.'

    cmdOut.returncode is the exit status of the called process. Typically 0
    means OK. A negative value -N indicates that the child was terminated by
    signal N (POSIX only).

    If the sub-process couldn't spawn at all (e.g executable not found), the
    results list will contain the Exception object instead of a
    SubprocessResult.

    You can find this list of results in context `cmdOut` after step completes.

    context['cmds'] will interpolate anything in curly braces for values
    found in context. So if your context looks like this:
        key1: value1
        key2: value2
        cmds:
            - mything --arg1 {key1}

    The cmd passed to the shell will be "mything --arg value1"
    """
    logger.debug("started")

    AsyncCmdStep(name=__name__, context=context, is_shell=True).run_step()

    logger.debug("done")
