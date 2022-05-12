"""pypyr step yaml for async subprocess commands - domain specific language."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Mapping, Sequence
import logging

from pypyr.aio.subproc import Command, Commands
from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
import pypyr.utils.types
from pypyr.subproc import SimpleCommandTypes

logger = logging.getLogger(__name__)

AsyncCommandTypes = SimpleCommandTypes + (Sequence,)


class AsyncCmdStep():
    """A pypyr step to run executables/commands concurrently as a subprocess.

    This models a step that takes config like this in simple syntax:
        cmds:
            - <<cmd string 1>>
            - <<cmd string 2>>

    All the commands will run concurrently, in parallel.

    OR, expanded syntax is as a dict
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
            - [./another-executable --arg, ./arb-executable arghere]
          save: False
          cwd: ./path/here

    As a list in simplified syntax:
        cmds:
          - my-executable --arg
          - ./another-executable --arg

    Any or all of the list items can use expanded syntax:
        cmds:
          - ./simple-cmd-here --arg1 value
          - run: cmd here
            save: False cwd: ./path/here
          - run:
              - my-executable --arg
              - ./another-executable --arg
            save: True
            cwd: ./path/here

    Any of the list items can in turn be a list. A sub-list will run in serial.

    In this example A, B.1 & C will start concurrently. B.2 will only run once
    B.1 is finished.

        cmds:
            - A
            - [B.1, B.2]
            - C

    If save is True, will save the output to context as cmdOut.

    cmdOut will be a list of pypyr.subproc.SubprocessResult objects, in order
    executed.

    SubprocessResult has the following properties:
    cmd: the cmd/args executed
    returncode: 0
    stdout: 'stdout str here. None if empty.'
    stderr: 'stderr str here. None if empty.'

    cmdOut.returncode is the exit status of the called process. Typically 0
    means OK. A negative value -N indicates that the child was terminated by
    signal N (POSIX only).

    The run_step method does the actual work. init parses the input yaml.

    Attributes:
        logger (logger): Logger instantiated by name of calling step.
        context: (pypyr.context.Context): The current pypyr Context.
        commands (pypyr.subproc.Commands): Commands to run as subprocess.
        is_shell (bool): True if subprocess should run through default shell.
        name (str): Name of calling step. Used for logging output & error
            messages.
    """

    def __init__(self,
                 name: str,
                 context: Context,
                 is_shell: bool = False) -> None:
        """Initialize the CmdStep.

        The step config in the context dict in simplified syntax:
            cmd: <<cmd string>>

        OR, as a dict in expanded syntax:
            cmd:
                run: str. mandatory. command + args to execute.
                save: bool. optional. defaults False. save output to cmdOut.
                cwd: str/path. optional. if specified, change the working
                     directory just for the duration of the command.

        `run` can be a single string, or it can be a list of string if there
        are multiple commands to execute with the same settings.

        OR, as a list:
            cmd:
                - my-executable --arg
                - ./another-executable --arg

        Any or all of the list items can be in expanded syntax.

        Args:
            name (str): Unique name for step. Likely __name__ of calling step.
            context (pypyr.context.Context): Look for step config in this
                context instance.
            is_shell (bool): Set to true to execute cmd through the default
                shell.
        """
        assert name, ("name parameter must exist for CmdStep.")
        assert context, ("context param must exist for CmdStep.")
        # this way, logs output as the calling step, which makes more sense
        # to end-user than a mystery steps.dsl.blah logging output.
        self.name = name
        self.logger = logging.getLogger(name)

        context.assert_key_has_value(key='cmds', caller=name)

        self.context = context
        self.is_shell = is_shell
        cmd_config = context.get_formatted('cmds')

        commands = Commands()
        if isinstance(cmd_config, SimpleCommandTypes):
            commands.append(Command(cmd_config, is_shell=is_shell))
        elif isinstance(cmd_config, Mapping):
            commands.append(self.create_command(cmd_config))
        elif isinstance(cmd_config, Sequence):
            for cmd in cmd_config:
                if isinstance(cmd, SimpleCommandTypes):
                    commands.append(Command(cmd, is_shell=is_shell))
                elif isinstance(cmd, Sequence):
                    commands.append(Command([cmd], is_shell=is_shell))
                elif isinstance(cmd, Mapping):
                    commands.append(self.create_command(cmd))
                else:
                    raise ContextError(
                        f"{cmd} in {name} cmds config is wrong.\n"
                        "Each list item should be either a simple string, or "
                        "a list to run in serial,\n"
                        "or a dict for expanded syntax:\n"
                        "cmds:\n"
                        "  - ./my-executable --arg\n"
                        "  - run:\n"
                        "      - ./another-executable --arg value\n"
                        "      - ./another-executable --arg value2\n"
                        "    cwd: ../mydir/subdir\n"
                        "  - run:\n"
                        "      - ./arb-executable1 --arg value1\n"
                        "      - [./arb-executable2.1, ./arb-executable2.2]\n"
                        "    cwd: ../mydir/arbdir\n"
                        "  - [./arb-executable3.1, ./arb-executable3.2]"
                    )
        else:
            raise ContextError(f"{name} cmds config should be either a list:\n"
                               "cmds:\n"
                               "  - ./my-executable --arg\n"
                               "  - subdir/executable --arg1\n\n"
                               "or a dictionary with a `run` sub-key:\n"
                               "cmds:\n"
                               "  run:\n"
                               "    - ./my-executable --arg\n"
                               "    - subdir/executable --arg1\n"
                               "  cwd: ./mydir\n\n"
                               "Any of the list items in root can be in "
                               "expanded syntax:\n"
                               "cmds:\n"
                               "  - ./my-executable --arg\n"
                               "  - subdir/executable --arg1\n"
                               "  - run:\n"
                               "      - ./arb-executable1 --arg value1\n"
                               "      - [./arb-executable2.1, "
                               "./arb-executable2.2]\n"
                               "    cwd: ../mydir/subdir\n"
                               "  - [./arb-executable3.1, ./arb-executable3.2]"
                               )

        self.commands: Commands = commands

    def create_command(self, cmd_input: Mapping) -> Command:
        """Create pypyr.aio.subproc.Command object from expanded step input."""
        try:
            cmd = cmd_input['run']  # can be str or list
            if not cmd:
                raise KeyInContextHasNoValueError(
                    f"cmds.run must have a value for {self.name}.\n"
                    "The `run` input should look something like this:\n"
                    "cmds:\n"
                    "  run:\n"
                    "    - ./arb-executable1 --arg value1\n"
                    "    - ./arb-executable2 --arg value2\n"
                    "  cwd: ../mydir/arbdir")
        except KeyError as err:
            raise KeyNotInContextError(
                f"cmds.run doesn't exist for {self.name}.\n"
                "The input should look like this in expanded syntax:\n"
                "cmds:\n"
                "  run:\n"
                "    - ./my-executable --arg\n"
                "    - subdir/executable --arg1\n"
                "  cwd: ./mydir\n\n"
                "If you're passing in a list of commands, each command should "
                "be a simple string,\n"
                "or a sub-list of commands to run in serial,\n"
                "or a dict with a `run` entry:\n"
                "cmds:\n"
                "  - ./my-executable --arg\n"
                "  - run: ./another-executable --arg value\n"
                "    cwd: ../mydir/subdir\n"
                "  - run:\n"
                "      - ./arb-executable1 --arg value1\n"
                "      - [./arb-executable2.1, ./arb-executable2.2]\n"
                "    cwd: ../mydir/arbdir\n"
                "  - [./arb-executable3.1, ./arb-executable3.2]"
            ) from err

        is_save = pypyr.utils.types.cast_to_bool(cmd_input.get('save', False))

        cwd = cmd_input.get('cwd')

        is_bytes = cmd_input.get('bytes')
        is_text = not is_bytes if is_save else False

        stdout = cmd_input.get('stdout')
        stderr = cmd_input.get('stderr')

        if is_save:
            if stderr or stderr:
                raise ContextError(
                    "You can't set `stdout` or `stderr` when `save` is True.")

        encoding = cmd_input.get('encoding')
        append = cmd_input.get('append', False)
        is_shell_override = cmd_input.get('shell', None)

        is_shell = (
            self.is_shell if is_shell_override is None else is_shell_override)

        return Command(cmd=cmd,
                       is_shell=is_shell,
                       cwd=cwd,
                       is_save=is_save,
                       is_text=is_text,
                       stdout=stdout,
                       stderr=stderr,
                       encoding=encoding,
                       append=append)

    def run_step(self) -> None:
        """Spawn subprocesses to run the commands asynchronously.

        If cmd.is_save==True, save aggregate result of all commands to context
        'cmdOut'.

        cmdOut will be a list of pypyr.subproc.SubprocessResult or Exception
        objects, in order executed.

        SubprocessResult has the following properties:
        cmd: the cmd/args executed
        returncode: 0
        stdout: 'stdout str here. None if empty.'
        stderr: 'stderr str here. None if empty.'
        """
        try:
            self.commands.run()
        finally:
            if self.commands.is_save:
                self.logger.debug("saving results to cmdOut")
                self.context['cmdOut'] = self.commands.results
            else:
                self.logger.debug(
                    "save is False: not saving results to cmdOut")
