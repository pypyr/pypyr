"""pypyr step yaml for subprocess commands - domain specific language."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Mapping, Sequence
import logging

from pypyr.context import Context
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)
import pypyr.utils.types
from pypyr.subproc import Command, SimpleCommandTypes

logger = logging.getLogger(__name__)


class CmdStep():
    """A pypyr step to run an executable or command as a subprocess.

    This models a step that takes config like this:
        cmd: <<cmd string>>

    OR, expanded syntax is as a dict
        cmd:
            run: str. mandatory. command + args to execute.
            save: bool. defaults False. save output to cmdOut. Treats output
                as text in the system's encoding and removes newlines at end.
            cwd: str/Pathlike. optional. Working directory for this command.
            bytes (bool): Default False. When `save` return output bytes from
                cmd unaltered, without applying any encoding & text newline
                processing.
            encoding (str): Default None. When `save`, decode cmd output with
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
        cmd:
          run:
            - my-executable --arg
            - cmd here
          save: False cwd: ./path/here

    OR, as a list in simplified syntax:
        cmd:
          - my-executable --arg
          - ./another-executable --arg

    Any or all of the list items can use expanded syntax:
        cmd:
          - ./simple-cmd-here --arg1 value
          - run: cmd here
            save: False cwd: ./path/here
          - run:
              - my-executable --arg
              - ./another-executable --arg
            save: True cwd: ./path/here

    If save is True, will save the output to context as follows:
        cmdOut:
            returncode: 0
            stdout: 'stdout str here. None if empty.'
            stderr: 'stderr str here. None if empty.'

    If the cmd input contains a list of executables, cmdOut will be a list of
    cmdOut objects, in order executed.

    cmdOut.returncode is the exit status of the called process. Typically 0
    means OK. A negative value -N indicates that the child was terminated by
    signal N (POSIX only).

    The run_step method does the actual work. init parses the input yaml.

    Attributes:
        logger (logger): Logger instantiated by name of calling step.
        context: (pypyr.context.Context): The current pypyr Context.
        commands (list[pypyr.subproc.Command]): Commands to run as subprocess.
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

        context.assert_key_has_value(key='cmd', caller=name)

        self.context = context
        self.is_shell = is_shell
        cmd_config = context.get_formatted('cmd')

        commands: list[Command] = []
        if isinstance(cmd_config, SimpleCommandTypes):
            commands.append(Command(cmd_config, is_shell=is_shell))
        elif isinstance(cmd_config, Mapping):
            commands.append(self.create_command(cmd_config))
        elif isinstance(cmd_config, Sequence):
            for cmd in cmd_config:
                if isinstance(cmd, SimpleCommandTypes):
                    commands.append(Command(cmd, is_shell=is_shell))
                elif isinstance(cmd, Mapping):
                    commands.append(self.create_command(cmd))
                else:
                    raise ContextError(
                        f"{cmd} in {name} cmd config is wrong.\n"
                        "Each list item should be either a simple string "
                        "or a dict for expanded syntax:\n"
                        "cmd:\n"
                        "  - my-executable --arg\n"
                        "  - run: another-executable --arg value\n"
                        "    cwd: ../mydir/subdir\n"
                        "  - run:\n"
                        "      - arb-executable1 --arg value1\n"
                        "      - arb-executable2 --arg value2\n"
                        "    cwd: ../mydir/arbdir")
        else:
            raise ContextError(f"{name} cmd config should be either a simple "
                               "string:\n"
                               "cmd: my-executable --arg\n\n"
                               "or a dictionary:\n"
                               "cmd:\n"
                               "  run: subdir/my-executable --arg\n"
                               "  cwd: ./mydir\n\n"
                               "or a list of commands:\n"
                               "cmd:\n"
                               "  - my-executable --arg\n"
                               "  - run: another-executable --arg value\n"
                               "    cwd: ../mydir/subdir")

        self.commands: list[Command] = commands

    def create_command(self, cmd_input: Mapping) -> Command:
        """Create a pypyr.subproc.Command object from expanded step input."""
        try:
            cmd = cmd_input['run']  # can be str or list
            if not cmd:
                raise KeyInContextHasNoValueError(
                    f"cmd.run must have a value for {self.name}.\n"
                    "The `run` input should look something like this:\n"
                    "cmd:\n"
                    "  run: my-executable-here --arg1\n"
                    "  cwd: ./mydir/subdir\n\n"
                    "Or, `run` could be a list of commands:\n"
                    "cmd:\n"
                    "  run:\n"
                    "    - arb-executable1 --arg value1\n"
                    "    - arb-executable2 --arg value2\n"
                    "  cwd: ../mydir/arbdir")
        except KeyError as err:
            raise KeyNotInContextError(
                f"cmd.run doesn't exist for {self.name}.\n"
                "The input should look like this in the simplified syntax:\n"
                "cmd: my-executable-here --arg1\n\n"
                "Or in the expanded syntax:\n"
                "cmd:\n"
                "  run: my-executable-here --arg1\n\n"
                "If you're passing in a list of commands, each command should "
                "be a simple string,\n"
                "or a dict with a `run` entry:\n"
                "cmd:\n"
                "  - my-executable --arg\n"
                "  - run: another-executable --arg value\n"
                "    cwd: ../mydir/subdir\n"
                "  - run:\n"
                "      - arb-executable1 --arg value1\n"
                "      - arb-executable2 --arg value2\n"
                "    cwd: ../mydir/arbdir"
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
        """Spawn a subprocess to run the command or program.

        If cmd.is_save==True, save result of each command to context 'cmdOut'.
        """
        results = []
        try:
            for cmd in self.commands:
                try:
                    cmd.run()
                finally:
                    if cmd.results:
                        results.extend(cmd.results)
        finally:
            if results:
                if len(results) == 1:
                    self.context['cmdOut'] = results[0]
                else:
                    self.context['cmdOut'] = results
