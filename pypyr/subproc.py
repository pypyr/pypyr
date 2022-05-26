"""Spawn subprocess synchronously."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Sequence
from contextlib import contextmanager
import logging
from os import PathLike
from pathlib import Path
import shlex
import subprocess

from pypyr.config import config
from pypyr.errors import ContextError, SubprocessError

logger = logging.getLogger(__name__)

SimpleCommandTypes = (str, bytes, PathLike)


class Command:
    """A subprocess run instruction. Use run() to spawn the subprocess.

    Attributes:
        cmd (str/bytes/Pathlike or list[str/bytes/Pathlike]): A str for a
            single run instruction, or a list of str for >1 run instructions.
        is_shell (bool): Invoke subprocess through the default shell.
        cwd (Path-like): Current working directory to this during execution.
        is_save (bool): Save output to self.results.
        is_text (bool): Treat stdin, stdout & stderr streams as text in the
            provided encoding, not bytes. This is only relevant when
            is_save is True.
        stdout (None | str | Pathlike): Write stdout here. None means inherit
            the parent's handle, '/dev/null' means to write to the null device,
            and a path will write to file.
        stderr (None | str | Pathlike): Write stderr here. None means inherit
            the parent's handle, '/dev/null' means to write to the null device,
            '/dev/stdout' redirects to stdout, and a path will write to file.
        encoding (str): Use this encoding on all the output streams. Default to
            the system's default encoding. Only applicable if is_save True.
        append (bool): If stdout/stderr refers to a file path, append to file
            rather than overwrite if it exists.
        results (list[SubprocessResult]): List of results. Populated with the
            result of each run instruction in `cmd`. Only when is_save is True.
    """

    def __init__(self,
                 cmd,
                 is_shell=False,
                 cwd=None,
                 is_save=False,
                 is_text=True,
                 stdout=None,
                 stderr=None,
                 encoding=None,
                 append=False):
        """Initialize the Cmd."""
        self.cmd = cmd
        self.is_shell = is_shell
        self.cwd = cwd
        self.is_save = is_save
        self.is_text = is_text if is_save else False

        if is_save:
            if stdout or stderr:
                raise ContextError(
                    "You can't set `stdout` or `stderr` when `save` is True.")
        self.stdout = stdout
        self.stderr = stderr
        self.encoding = encoding if encoding else config.default_cmd_encoding
        self.append = append

        self.results: list[SubprocessResult] = []

    @contextmanager
    def output_handles(self):
        """Return stdout + stderr output handles for subprocess.

        If self.stdout or self.stderr are None, will return None for whichever
        is None. This will result in the subprocess using the parent's handler
        for that output device.

        If self.stdout or self.stderr refers to a path, will open the file(s)
        at the given location for writing. Will create parent directories if
        these do not exist. self.append controls whether to overwrite or append
        files. Set self.encoding to write in text mode in the given encoding,
        otherwise the file handle opens in binary mode.

        The context manager will close the file handles (if any) when it exits.

        If self.stdout or self.stderr are the special values '/dev/null' or
        '/dev/stdout', will return the appropriate subprocess constants for
        these.

        Returns:
            (stdout, stderr): stdout & stderr handles to use when executing
                this command as a subprocess.
        """
        stdout = self.stdout
        stderr = self.stderr

        # fast short-circuit when no processing necessary
        if not stdout and not stderr:
            logger.debug("stdout & stderr inheriting from parent process.")
            yield stdout, stderr
        else:
            # append or overwrite
            mode = 'ab' if self.append else 'wb'
            files = []

            try:
                # stdout
                if stdout == '/dev/null':
                    logger.debug("redirecting stdout to /dev/null")
                    stdout = subprocess.DEVNULL
                elif stdout:
                    # by elimination, it's a path
                    logger.debug("writing stdout to %s in mode '%s'",
                                 stdout, mode)
                    Path(stdout).parent.mkdir(parents=True, exist_ok=True)
                    stdout = open(stdout, mode=mode)
                    files.append(stdout)

                #  stderr
                if stderr == '/dev/null':
                    logger.debug("redirecting stderr to /dev/null")
                    stderr = subprocess.DEVNULL
                elif stderr == '/dev/stdout':
                    logger.debug("redirecting stderr to /dev/stdout")
                    stderr = subprocess.STDOUT
                elif stderr:
                    # by elimination, it's a path
                    logger.debug("writing stderr to %s in mode '%s'",
                                 stderr, mode)
                    Path(stderr).parent.mkdir(parents=True, exist_ok=True)
                    stderr = open(stderr, mode=mode)
                    files.append(stderr)

                yield stdout, stderr
            finally:
                for f in files:
                    logger.debug("closing cmd file output %s", f.name)
                    f.close()

    def run(self):
        """Run the command as a subprocess.

        Raises:
            pypyr.errors.ContextError: The cmd executable instruction is
                formatted incorrectly.
            subprocess.CalledProcessError: Error executing the subprocess.
            FileNotFoundError: The system could not find the executable. It
                might not be on $PATH, or the path to the executable might be
                wrong.
        """
        cmd = self.cmd

        # this here because all outputs for this cmd write to the same
        # device/file handles - whether single cmd or list of commands.
        with self.output_handles() as (stdout, stderr):
            if isinstance(cmd, SimpleCommandTypes):
                # just one command, run as is
                self._run(cmd, stdout, stderr)
            elif isinstance(cmd, Sequence):
                # str explicitly checked before in if, so Sequence won't be str
                # except weirdness if passing bytearray (ByteString), but why
                # would you?
                for c in cmd:
                    # run each command in list of commands
                    self._run(c, stdout, stderr)
            else:
                raise ContextError(
                    f"{cmd} cmd should be either a simple string:\n"
                    "cmd: my-executable --arg\n\n"
                    "Or in the expanded syntax, set `run` to a string:\n\n"
                    "cmd:\n"
                    "  run: my-executable --arg\n"
                    "  cwd: ./mydir\n\n"
                    "Or set run to a list of commands:\n"
                    "cmd:\n"
                    "  run:\n"
                    "    - my-executable --arg\n"
                    "    - another-executable --arg2\n"
                    "  cwd: ../mydir/subdir")

    def _run(self, cmd, stdout=None, stderr=None):
        """Spawn subprocess for cmd with stdout + stderr output streams.

        If self.save is True, will append the completed process results to
        self.results, for both success and failure. Will strip trailing
        whitespace from output.

        Thereafter will raise an exception if anything had gone wrong with the
        subprocess.

        Args:
            cmd (str): The executable + args to spawn subprocess.
            stdout: Write stdout here. This can be None (attach to parent
                    process), an open file handle, or subprocess.DEVNULL.
            stderr: Write stderr here. This can be None (attach to parent
                    process), an open file handle, or subprocess.DEVNULL, or
                    subprocess.STDOUT to redirect to stdout.

        Raises:
            subprocess.CalledProcessError: Error executing the subprocess.
            FileNotFoundError: The system could not find the executable. It
                might not be on $PATH, or the path to the executable might be
                wrong.
        """
        if self.cwd:
            logger.debug("Processing command string in dir %s: %s",
                         self.cwd, self.cmd)
        else:
            logger.debug("Processing command string: %s", cmd)

        # why? If shell is True, python docs recommend passing args as a string
        # rather than as a sequence.
        # But not on windows, because windows API wants strings, not sequences.
        args = cmd if (
            self.is_shell or config.is_windows) else shlex.split(cmd)

        if self.is_save:
            # errs from _inside_ the subprocess will go to stderr and raise
            # via check_returncode. errs finding the executable will raise
            # right here - i.e won't end up in cmdOut.
            completed_process = subprocess.run(args,
                                               capture_output=True,
                                               cwd=self.cwd,
                                               encoding=self.encoding,
                                               shell=self.is_shell,
                                               text=self.is_text)

            stdout = completed_process.stdout
            stderr = completed_process.stderr

            if self.is_text:
                if stdout:
                    stdout = stdout.rstrip()
                if stderr:
                    stderr = stderr.rstrip()

            out = SubprocessResult(cmd=args,
                                   returncode=completed_process.returncode,
                                   stdout=stdout,
                                   stderr=stderr)

            # when capture is true, output doesn't write to stdout
            logger.info("stdout: %s", stdout)
            if stderr:
                logger.error("stderr: %s", stderr)

            # save output before checking/raising err that kicks out of method
            self.results.append(out)
            # don't swallow the error, because it's the Step swallow decorator
            # responsibility to decide to ignore or not.
            completed_process.check_returncode()
        else:
            # check=True throws CalledProcessError if exit code != 0
            subprocess.run(args,
                           check=True,
                           cwd=self.cwd,
                           shell=self.is_shell,
                           stdout=stdout,
                           stderr=stderr)

    def __eq__(self, other):
        """Check equality for all attributes."""
        if self is other:
            return True

        if type(other) is Command:
            return self.__dict__ == other.__dict__

        return NotImplemented


class SubprocessResult():
    """Result from a subprocess invocation.

    Attributes:
      cmd: The list or str args passed to the subprocess run instruction.
      returncode: The exit code of the process, negative for signals.
      stdout: The standard output (None if not captured).
      stderr: The standard error (None if not captured).

    Will also getitem in a dict-like way like r['returncode'] where dict is:
    {
        'returncode': proc.returncode,
        'stdout': stdout,
        'stderr': stderr
    }

    The dict-like accessor is only there for backwards compatibility, don't
    use it for anything new.
    """

    def __init__(self, cmd, returncode, stdout=None, stderr=None):
        """Initialize result."""
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __getitem__(self, key):
        """Allow dict-like r['returncode'] access for backwards compat."""
        return self.__dict__[key]

    def __repr__(self) -> str:
        """Return repr."""
        args = ['cmd={!r}'.format(self.cmd),
                'returncode={!r}'.format(self.returncode)]
        if self.stdout is not None:
            args.append('stdout={!r}'.format(self.stdout))
        if self.stderr is not None:
            args.append('stderr={!r}'.format(self.stderr))
        return "{}({})".format(type(self).__name__, ', '.join(args))

    def __str__(self) -> str:
        """Get user friendly string."""
        return f"""\
cmd: {self.cmd}
returncode: {self.returncode}
stdout: {self.stdout}
stderr: {self.stderr}
"""

    def check_returncode(self) -> SubprocessError | None:
        """Return SubprocessError if the exit code is non-zero.

        This does not raise the error, it just returns it.

        Returns:
            None if no return code 0.
            SubprocessError if return code != 0.
        """
        if self.returncode:
            return SubprocessError(returncode=self.returncode,
                                   cmd=self.cmd,
                                   stdout=self.stdout,
                                   stderr=self.stderr)
        return None
