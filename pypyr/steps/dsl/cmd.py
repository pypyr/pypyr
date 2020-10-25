"""pypyr step yaml definition for commands - domain specific language."""
import shlex
import subprocess
import logging
from pypyr.errors import ContextError
from pypyr.utils import types

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


class CmdStep():
    """A pypyr step that represents a command runner step.

    This models a step that takes config like this:
        cmd: <<cmd string>>

        OR, as a dict
        cmd:
            run: str. mandatory. command + args to execute.
            save: bool. defaults False. save output to cmdOut.

    If save is True, will save the output to context as follows:
        cmdOut:
            returncode: 0
            stdout: 'stdout str here. None if empty.'
            stderr: 'stderr str here. None if empty.'

    cmdOut.returncode is the exit status of the called process. Typically 0
    means OK. A negative value -N indicates that the child was terminated by
    signal N (POSIX only).

    The run_step method does the actual work. init loads the yaml.
    """

    def __init__(self, name, context):
        """Initialize the CmdStep.

        The step config in the context dict looks like this:
            cmd: <<cmd string>>

            OR, as a dict
            cmd:
                run: str. mandatory. command + args to execute.
                save: bool. optional. defaults False. save output to cmdOut.
                cwd: str/path. optional. if specified, change the working
                     directory just for the duration of the command.

        Args:
            name: Unique name for step. Likely __name__ of calling step.
            context: pypyr.context.Context. Look for config in this context
                     instance.

        """
        assert name, ("name parameter must exist for CmdStep.")
        assert context, ("context param must exist for CmdStep.")
        # this way, logs output as the calling step, which makes more sense
        # to end-user than a mystery steps.dsl.blah logging output.
        self.logger = logging.getLogger(name)

        context.assert_key_has_value(key='cmd', caller=name)

        self.context = context
        self.is_save = False

        cmd_config = context.get_formatted('cmd')

        if isinstance(cmd_config, str):
            self.cmd_text = cmd_config
            self.cwd = None
            self.logger.debug("Processing command string: %s", cmd_config)
        elif isinstance(cmd_config, dict):
            context.assert_child_key_has_value(parent='cmd',
                                               child='run',
                                               caller=name)

            self.cmd_text = cmd_config['run']
            self.is_save = types.cast_to_bool(cmd_config.get('save', False))

            cwd_string = cmd_config.get('cwd', None)
            if cwd_string:
                self.cwd = cwd_string
                self.logger.debug("Processing command string in dir "
                                  "%s: %s", self.cwd, self.cmd_text)
            else:
                self.cwd = None
                self.logger.debug("Processing command string: %s",
                                  self.cmd_text)

        else:
            raise ContextError(f"{name} cmd config should be either a simple "
                               "string cmd='mycommandhere' or a dictionary "
                               "cmd={'run': 'mycommandhere', 'save': False}.")

    def run_step(self, is_shell):
        """Run a command.

        Runs a program or executable. If is_shell is True, executes the command
        through the shell.

        Args:
            is_shell: bool. defaults False. Set to true to execute cmd through
                      the default shell.
        """
        assert is_shell is not None, ("is_shell param must exist for CmdStep.")

        # why? If shell is True, it is recommended to pass args as a string
        # rather than as a sequence.
        if is_shell:
            args = self.cmd_text
        else:
            args = shlex.split(self.cmd_text)

        if self.is_save:
            completed_process = subprocess.run(args,
                                               cwd=self.cwd,
                                               shell=is_shell,
                                               # capture_output=True,only>py3.7
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               # text=True, only>=py3.7,
                                               universal_newlines=True)
            self.context['cmdOut'] = {
                'returncode': completed_process.returncode,
                'stdout': (completed_process.stdout.rstrip()
                           if completed_process.stdout else None),
                'stderr': (completed_process.stderr.rstrip()
                           if completed_process.stderr else None)
            }

            # when capture is true, output doesn't write to stdout
            self.logger.info("stdout: %s", completed_process.stdout)
            if completed_process.stderr:
                self.logger.error("stderr: %s", completed_process.stderr)

            # don't swallow the error, because it's the Step swallow decorator
            # responsibility to decide to ignore or not.
            completed_process.check_returncode()
        else:
            # check=True throws CalledProcessError if exit code != 0
            subprocess.run(args, shell=is_shell, check=True, cwd=self.cwd)
