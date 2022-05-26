"""Spawn subprocess asynchronously."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
import asyncio
from asyncio import subprocess
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
import locale
import logging
from pathlib import Path
import shlex

from pypyr.config import config
from pypyr.errors import ContextError, MultiError
from pypyr.subproc import SimpleCommandTypes, SubprocessResult

logger = logging.getLogger(__name__)

# region windows shlex
is_windows = config.is_windows

DEFAULT_ENCODING = (config.default_cmd_encoding
                    if config.default_cmd_encoding
                    else locale.getpreferredencoding(False))

# this code is in fact covered when run on windows (during CI)
# set no cover so no complaining from coverage on posix
if is_windows:  # pragma: no cover
    from ctypes.wintypes import LPWSTR, HLOCAL
    from ctypes import windll, c_int, POINTER, byref  # type: ignore

    CommandLineToArgvW = windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.restype = POINTER(LPWSTR)

    LocalFree = windll.kernel32.LocalFree
    LocalFree.argtypes = [HLOCAL]
    LocalFree.restype = HLOCAL


def winshlex_split(cmd: str) -> list[str]:  # pragma: no cover
    """Split cmd string into args using Windows api."""
    num_args = c_int()
    lp_args = CommandLineToArgvW(cmd, byref(num_args))

    # copy response
    args = [lp_args[i] for i in range(num_args.value)]

    # must free allocated block of contiguous memory, prevent leaks
    if LocalFree(lp_args):
        # return value is None when LocalFree succeeds
        # on fail return value is handle to the local memory object
        raise RuntimeError(
            f"Failed to release {lp_args} after winddll.shell32 "
            + "CommandLineToArgvW")

    return args

# endregion windows shlex


shlexer = winshlex_split if is_windows else shlex.split


class Command:
    """A subprocess run instruction. Use async run() to spawn the subprocess.

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
            rather than overwrite if it exists. Only relevant when is_save
            False.
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
            self.stdout = self.stderr = subprocess.PIPE
        else:
            self.stdout = stdout
            self.stderr = stderr
        self.encoding = encoding if encoding else DEFAULT_ENCODING
        self.append = append

        self._results: list[SubprocessResult | Exception | list] = []

    @property
    def results(self) -> list[SubprocessResult | Exception | list]:
        """Results of this Command after run()."""
        return self._results

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

        If self.stdout or self.stderr are the special values subprocess.PIPE,
        '/dev/null' or '/dev/stdout', will return the appropriate subprocess
        constants for these.

        Returns:
            (stdout, stderr): stdout & stderr handles to use when executing
                this command as a subprocess.
        """
        stdout = self.stdout
        stderr = self.stderr
        # fast short-circuit when no processing necessary
        if not stdout and not stderr:
            #  this works because stdout/stderr will be PIPE when capturing
            logger.debug("stdout & stderr attaching to parent process.")
            yield stdout, stderr
        else:
            # append or overwrite
            mode = 'ab' if self.append else 'wb'
            files = []
            try:
                # stdout
                if stdout == subprocess.PIPE:
                    logger.debug("capturing stdout")
                elif stdout == '/dev/null':
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
                if stderr == subprocess.PIPE:
                    logger.debug("capturing stderr")
                elif stderr == '/dev/null':
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

    def parse_results(self) -> list[Exception]:
        """Parse subprocess output for errors.

        Errors are likely to be SubprocessError where returncode != 0.

        If there were problems getting to the subprocess itself (i.e it
        couldn't even run), likely to be a PermissionError or OSError.

        This does not raise any exceptions, it just returns a list of them.

        Returns:
            list[Exception]: Flattened list of Exception objects.
        """
        errors = []
        for result in self._results:
            for error in self._parse_result(result):
                errors.append(error)
        return errors

    def _parse_result(self,
                      result: SubprocessResult | Exception | list
                      ) -> Iterator[Exception]:
        """Parse results recursively looking for errors."""
        if isinstance(result, Exception):
            yield result
        elif isinstance(result, SubprocessResult):
            error = result.check_returncode()
            if error:
                yield error
        elif isinstance(result, list):
            for nested_result in result:
                yield from self._parse_result(nested_result)
        else:
            # this really should be unreachable.
            raise TypeError(
                f"{result} is {type(result)}.\n"
                + "It should be SubprocessResult | Exception | "
                + "list[SubprocessResult | Exception].")
        # don't just add stuff here! remember those yields further up!

    async def run(self) -> None:
        """Run the command asynchronously as a subprocess.

        Do NOT raise exceptions in here. Add exceptions to self.results
        instead.

        Typical exceptions that end up in `results`:
            pypyr.errors.ContextError: The cmd executable instruction is
                formatted incorrectly.
            subprocess.CalledProcessError: Error executing the subprocess.
            FileNotFoundError: The system could not find the executable. It
                might not be on $PATH, or the path to the executable might be
                wrong.
        """
        cmd = self.cmd
        try:
            # this here because all outputs for this cmd write to the same
            # device/file handles - whether single cmd or list of commands.
            with self.output_handles() as (stdout, stderr):
                if isinstance(cmd, SimpleCommandTypes):
                    # just one command, run as is
                    try:
                        result = await self._run(cmd, stdout, stderr)
                    except Exception as ex:
                        # mypy currently doesn't like re-using local var name
                        result = ex  # type: ignore

                    self._results.append(result)
                elif isinstance(cmd, Sequence):
                    # Sequence won't be str - explicitly checked before in if
                    # except weirdness if passing bytearray (ByteString), but
                    # why would you?
                    tasks = [self._run(c, stdout, stderr) for c in cmd]
                    results = await asyncio.gather(*tasks,
                                                   return_exceptions=True)
                    # extend results shared state here coz concurrent now done
                    self._results.extend(results)
                else:
                    err = ContextError(
                        f"{cmd} cmds input.\n"
                        "Each command should be a simple string, or a "
                        "sub-list to run in serial:\n"
                        "cmds:\n"
                        "  - ./my-executable --arg\n"
                        "  - ./another-executable --arg\n"
                        "  - [./executableA.1, ./executableA.2]\n\n"
                        "Or in the expanded syntax, set `run` to a list:\n"
                        "cmds:\n"
                        "  run:\n"
                        "    - ./my-executable --arg\n"
                        "    - ./another-executable --arg\n"
                        "    - [./executableA.1, ./executableA.2]\n"
                        "  cwd: ./mydir")
                    self._results.append(err)
        except Exception as ex:
            # instead of raising exception, any errs MUST be available on
            # `results` for this particular cmd (otherwise caller gather of >1
            # commands won't know _which_ cmd raised the err.)
            self._results.append(ex)

    async def _run(self, cmd,
                   stdout=None,
                   stderr=None
                   ) -> SubprocessResult | list[SubprocessResult | Exception]:
        """Spawn subprocess for cmd with stdout + stderr output streams.

        If self.is_save is True, will append the completed process results to
        self.results, for both success and failure. Will strip trailing
        whitespace from output.

        A non-zero returncode will not raise error, it returns a
                SubprocessResult with the details instead. Will raise error
                if subprocess couldn't even execute at all.

        Args:
            cmd (str | Pathlike | list): The executable + args to spawn as
                                a subprocess. If list, will execute cmds in
                                list in serial.
            stdout: Write stdout here. This can be None (attach to parent
                    process), an open file handle, subprocess.PIPE (to capture)
                    or subprocess.DEVNULL.
            stderr: Write stderr here. This can be None (attach to parent
                    process), an open file handle, or subprocess.PIPE (to
                    capture) or subprocess.DEVNULL, or subprocess.STDOUT to
                    redirect to stdout.

        Returns:
            A SubprocessResult or list of SubprocessResult when cmd is a list
            of serial commands.

        Raises:
            subprocess.CalledProcessError: Error executing the subprocess.
            FileNotFoundError: The system could not find the executable. It
                might not be on $PATH, or the path to the executable might be
                wrong.
        """
        if isinstance(cmd, (list, tuple)):
            logger.debug(
                "async %s is a series of commands that will run in serial",
                cmd)
            results: list[SubprocessResult | Exception] = []
            try:
                for serial_cmd in cmd:
                    result = await self._spawn(serial_cmd,
                                               stdout=stdout,
                                               stderr=stderr)
                    results.append(result)
                    # don't proceed to next serial cmd if return code != 0
                    if result.returncode:
                        break
            except Exception as ex:
                # need to save results as they happen, so if later in sequence
                # fails, can still return results of preceding serial cmds
                results.append(ex)
            return results

        return await self._spawn(cmd, stdout=stdout, stderr=stderr)

    async def _spawn(self, cmd, stdout, stderr) -> SubprocessResult:
        if self.cwd:
            logger.debug("Processing command string in dir %s: %s",
                         self.cwd, self.cmd)
        else:
            logger.debug("Processing command string: %s", cmd)

        # errs from _inside_ the subprocess will go to stderr and raise
        # via check_returncode. errs finding the executable will raise
        # right here.
        if self.is_shell:
            proc = await asyncio.create_subprocess_shell(cmd,
                                                         stdout=stdout,
                                                         stderr=stderr,
                                                         cwd=self.cwd)
        else:
            cmd = shlexer(cmd)  # type: ignore
            logger.debug("arg split is: %s", cmd)
            proc = await asyncio.create_subprocess_exec(cmd[0],
                                                        *cmd[1:],
                                                        stdout=stdout,
                                                        stderr=stderr,
                                                        cwd=self.cwd)

        stdout_data, stderr_data = await proc.communicate()

        if self.is_save:
            if self.is_text:
                if stdout_data:
                    stdout_data = stdout_data.decode(
                        self.encoding).rstrip()  # type: ignore

                if stderr_data:
                    stderr_data = stderr_data.decode(
                        self.encoding).rstrip()  # type: ignore

        return SubprocessResult(cmd=cmd, returncode=proc.returncode,
                                stdout=stdout_data, stderr=stderr_data)

    def __eq__(self, other):
        """Check equality for all attributes."""
        if self is other:
            return True

        if type(other) is Command:
            return self.__dict__ == other.__dict__

        return NotImplemented


class Commands():
    """Execute a bunch of Command objects asynchronously.

    Use .append to add a Command to run.

    run() runs every Command appended with .append() in parallel.

    Check results with the `results` property.
    """

    def __init__(self) -> None:
        """Initialize commands to run asynchronously."""
        self.commands: list[Command] = []
        self._results: list[SubprocessResult | Exception | list] = []  # None
        self._is_save: bool = False

    def __getitem__(self, index: int) -> Command:
        """Get Command in collection by index."""
        return self.commands[index]

    def __iter__(self) -> Iterator[Command]:
        """Allow iteration through Command instances contained in Commands."""
        return iter(self.commands)

    def __len__(self) -> int:
        """Length (count) of Command instances in Commands."""
        return len(self.commands)

    def append(self, cmd: Command) -> None:
        """Append a Command to run asynchronously."""
        if cmd.is_save and not self._is_save:
            self._is_save = True
        self.commands.append(cmd)

    @property
    def is_save(self) -> bool:
        """Is true when any of the Commands to process has is_save==True."""
        return self._is_save

    @property
    def results(self) -> list[SubprocessResult | Exception
                              | list[SubprocessResult | Exception]]:
        """Return the aggregate list of results for all the command runs.

        Only contains results where a Command.is_save == True.
        """
        return self._results

    def run(self) -> None:
        """Run all commands as asynchronous subprocesses.

        This is the method that does the work. It contains an asyncio.run(),
        so you can't call this from an already existing event-loop.

        When this is done, whether it raises an exception or not, you can check
        `results` on the instance to see outputs for each command.

        Raises:
            pypyr.errors.MultiError: Aggregate error containing a list of
                any/all errors that any of the subprocesses might have raised.
        """
        asyncio.run(self._run())
        errors = []
        for cmd in self.commands:
            if cmd.is_save:
                self._results.extend(cmd._results)
            errs = cmd.parse_results()
            if errs:
                errors.extend(errs)

        if errors:
            raise MultiError(("The following error(s) occurred while running "
                              + "the async commands:"),
                             errors)

    async def _run(self) -> None:
        """Run all commands asynchronously & gather results."""
        tasks = [cmd.run() for cmd in self.commands]
        await asyncio.gather(*tasks)

    def __eq__(self, other):
        """Check equality for Command contained in commands list."""
        if self is other:
            return True

        if type(other) is Commands:
            return self.commands == other.commands

        return NotImplemented
