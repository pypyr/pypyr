"""Custom exceptions for pypyr.

All pypyr specific exceptions derive from Error.

Do NOT import any other pypyr modules here. This is to prevent circular
imports. Every other module in pypyr potentially uses this module.
"""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Iterator, Sequence
import signal


def get_error_name(error):
    """Return canonical error name as string.

    For builtin errors like ValueError or Exception, will return the bare
    name, like ValueError or Exception.

    For all other exceptions, will return modulename.errorname, such as
    arbpackage.mod.myerror

    Args:
        error: Exception object.

    Returns:
        str. Canonical error name.

    """
    error_type = type(error)
    if error_type.__module__ in ['__main__', 'builtins']:
        return error_type.__name__
    else:
        return f'{error_type.__module__}.{error_type.__name__}'


class Error(Exception):
    """Base class for all pypyr exceptions."""


class ConfigError(Error):
    """Error loading configuration."""


class ContextError(Error):
    """Error in the pypyr context."""


class HandledError(Error):
    """Error that has already been saved to errors context collection."""


class KeyInContextHasNoValueError(ContextError):
    """pypyr context[key] doesn't have a value."""


class KeyNotInContextError(ContextError, KeyError):
    """Key not found in the pypyr context."""

    def __str__(self):
        """Avoid KeyError custom error formatting."""
        return super(Exception, self).__str__()


class LoopMaxExhaustedError(Error):
    """Max attempts reached during looping."""


class MultiError(Error):
    """Aggregate exception."""

    def __init__(self, message: str | None = None,
                 errors: list[Exception] | None = None):
        """Create a MultiError exception."""
        super().__init__(message, errors)
        self.message = message
        self.errors: list[Exception] = errors if errors else []

    def append(self, error: Exception) -> None:
        """Add exception to the MultiError."""
        self.errors.append(error)

    def extend(self, errors: Sequence) -> None:
        """Extend input errors into MultiError list."""
        self.errors.extend(errors)

    @property
    def has_errors(self) -> bool:
        """Return True if contains exceptions."""
        return len(self.errors) > 0

    def __getitem__(self, index: int) -> Exception:
        """Get exception by index."""
        return self.errors[index]

    def __iter__(self) -> Iterator[Exception]:
        """Iterate through the exceptions in the MultiError."""
        return iter(self.errors)

    def __len__(self) -> int:
        """Get number of errors contained in the MultiError."""
        return len(self.errors)

    def __repr__(self) -> str:
        """Get string repr."""
        args = []
        if self.message:
            args.append(f'message={repr(self.message)}')

        if self.errors:
            args.append(f'errors={repr(self.errors)}')

        args_str = ', '.join(args)
        return f"{type(self).__name__}({args_str})"

    def __str__(self) -> str:
        """Get human friendly string."""
        msg = f'{self.message}' if self.message else (
            'Multiple error(s) occurred:' if len(self.errors) > 1
            else 'An error occurred:')
        errors = "\n".join([f'{type(e).__name__}: {e}' for e in self.errors])
        return f"{msg}\n{errors}" if errors else msg


class PipelineDefinitionError(Error):
    """Pipeline definition incorrect. Likely a yaml error."""


class PipelineNotFoundError(Error):
    """Pipeline not found in working dir or in pypyr install dir."""


class PlugInError(Error):
    """Pypyr plug - ins should sub - class this."""


class PyModuleNotFoundError(Error, ModuleNotFoundError):
    """Could not load python module because it wasn't found."""


class SubprocessError(Error):
    """Error on executable or shell run as a sub-process.

    Attributes:
        cmd (str | bytes | Path): The cmd or shell instruction that caused
            the error.
        returncode (int): Return code from sub-process. 0 usually means OK.
        stdout (str | bytes | None): stdout output, if any.
        stderr (str | bytes | None): stderr output, if any.
    """

    def __init__(self, returncode, cmd, stdout=None, stderr=None) -> None:
        """Initialize class."""
        super().__init__(returncode, cmd, stdout, stderr)
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self) -> str:
        """Convert to repr."""
        args = ['returncode={!r}'.format(self.returncode),
                'cmd={!r}'.format(self.cmd)]
        if self.stdout is not None:
            args.append('stdout={!r}'.format(self.stdout))
        if self.stderr is not None:
            args.append('stderr={!r}'.format(self.stderr))
        return "{}({})".format(type(self).__name__, ', '.join(args))

    def __str__(self) -> str:
        """Convert to string."""
        if self.returncode and self.returncode < 0:
            try:
                sig = repr(signal.Signals(-self.returncode))
                return f"Command '{self.cmd}' died with {sig}."
            except ValueError:
                return (f"Command '{self.cmd}' died with unknown signal "
                        + f"{-self.returncode}.")
        else:
            stderr = f" stderr: {self.stderr}" if self.stderr else ''
            return (f"Command '{self.cmd}' returned non-zero exit status "
                    + f"{self.returncode}.{stderr}")

# region Control of Flow Instructions


class Stop(Error):
    """Control of flow. Stop all execution."""


class StopPipeline(Stop):
    """Control of flow. Stop current pipeline execution."""


class StopStepGroup(Stop):
    """Control of flow. Stop current step - group execution."""


class ControlOfFlowInstruction(Error):
    """Control of flow instructions should inherit from this.

    Attributes:
        groups: list of str. List of step - groups to execute.
        success_group: str. Step - group to execute on success condition.
        failure_group: str. Step - group to execute on failure condition.
        original_config: tuple. (key, value). Key-Value pair of context dict
                        item used as input on the step that created this
                        ControlOfFlowInstruction.
    """

    def __init__(self, groups, success_group, failure_group, original_config):
        """Initialize the control of flow instruction.

        Args:
            groups: list of str. List of step - groups to execute.
            success_group: str. Step - group to execute on success condition.
            failure_group: str. Step - group to execute on failure condition.
            original_config: tuple. (key, value). Key/Value pair of Context
                             input for the control-of-flow step.
        """
        self.groups = groups
        self.success_group = success_group
        self.failure_group = failure_group
        self.original_config = original_config


class Call(ControlOfFlowInstruction):
    """Stop current step, call a new step group, resume current step after."""


class Jump(ControlOfFlowInstruction):
    """Stop step execution and jump to a new step group."""

# endregion Control of Flow Instructions
