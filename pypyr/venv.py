"""Create and manage stdlib venv aka virtual environments."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import Executor, Future
import logging
import os
from os import PathLike
import os.path
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace
from venv import EnvBuilder

from pypyr.errors import ContextError, Error

logger = logging.getLogger(__name__)

CORE_VENV_DEPS = ('pip', 'setuptools')
SIMPLE_INPUT_TYPE = (str, PathLike)
IS_BEFORE_PY_3_9 = sys.version_info < (3, 9)


class VenvCreator():
    """Encapsulate python venv module functionality to create venvs."""

    DEFAULT_USE_SYMLINKS = False if os.name == 'nt' else True
    EXCEPTION_UPGRADE_CLEAR = """Error creating {path!s}.
You cannot set both upgrade and clear together for a venv."""

    EXCEPTION_NO_PIP = """Error creating {path!s}.
You cannot set `pip` or `upgrade_pip` when `with_pip` is False."""

    def __init__(self,
                 path: str | PathLike,
                 pip_extras: str = None,
                 system_site_packages: bool = False,
                 clear: bool = False,
                 symlinks: bool | None = None,
                 upgrade: bool = False,
                 with_pip: bool = True,
                 prompt: str = None,
                 upgrade_pip: bool = True,
                 is_quiet: bool = False) -> None:
        """Initialize VenvCreator."""
        if upgrade and clear:
            raise ContextError(
                VenvCreator.EXCEPTION_UPGRADE_CLEAR.format(path=path))

        if with_pip is False:
            upgrade_pip = False

            if pip_extras:
                raise ContextError(
                    VenvCreator.EXCEPTION_NO_PIP.format(path=path))

        self.path = str(Path(path).expanduser().resolve())
        self.pip_extras = pip_extras
        self.upgrade_pip = upgrade_pip
        self.with_pip = with_pip
        self.is_quiet = is_quiet
        if symlinks is None:
            symlinks = VenvCreator.DEFAULT_USE_SYMLINKS
            logger.debug("venv using symlinks: %s", symlinks)

        # env_builder always sets upgrade_deps False to prevent the pip install
        # running in parallel in ThreadPoolExecutor. If upgrade_pip is True,
        # will do the pip upgrade as part of install_dependencies in serial
        # AFTER the parallel env creation is complete.
        self._env_builder = EnvBuilderWithExtraDeps(
            system_site_packages=system_site_packages,
            clear=clear,
            symlinks=symlinks,
            upgrade=upgrade,
            with_pip=with_pip,
            prompt=prompt,
            upgrade_deps=False,
            is_quiet=is_quiet)

        self._future: Future | None = None
        self._is_done = False

    def check_result(self) -> Exception | None:
        """Return exception if any. None means success."""
        if self._future:
            ex = self._future.exception()
            if ex is None or isinstance(ex, Exception):
                return ex
            else:
                # raise BaseException immediately - KeyboardInterrupt etc.
                # not sure to what degree this is just mypy bleating over
                # nothing (future.exception typed as BaseException not
                # Exception.)
                raise ex
        else:
            raise Error(
                "You can only call check_result after create_in_executor. "
                + f"Error creating venv {self.path!s}"
            )

    def create(self) -> None:
        """Create the venv on disk.

        This method MUST be safe for parallel execution.

        So no pip install, unless pip in future support parallel execution.
        """
        logger.debug("started")
        self._env_builder.create(self.path)
        self._is_done = True
        logger.debug("done create venv path %s", self.path)

    def create_in_executor(self, executor: Executor) -> None:
        """Run create in the provided executor."""
        logger.debug("starting venv creation: %s", self.path)
        self._future = executor.submit(self.create)

    def install_dependencies(self) -> None:
        """Upgrade pip & install extra dependencies. Run me in serial."""
        logger.debug("started")
        if not self._is_done:
            # you really shouldn't end up here, unless API user is calling this
            # out of sequence, thus raise hard exception.
            raise Error(
                "you can't call install_dependencies before the environment "
                + f"is installed successfully for {self.path!s}.")

        env_builder = self._env_builder
        if not env_builder.with_pip:
            raise Error(
                f"you can't install extra dependencies into {self.path!s} "
                + "because with_pip is False.")

        if self.upgrade_pip:
            # upgrades pip & setuptools
            logger.debug("upgrading pip & setuptools in %s", self.path)
            env_builder.upgrade_dependencies(self._env_builder.context)

        if not self.pip_extras:
            logger.debug(
                "done - no extra dependencies to install for path %s",
                self.path)
            return

        env_builder.pip_install_extras(self.pip_extras)

        logger.debug("done")

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Iterable[VenvCreator]:
        """Create VenvCreator from a dict/mapping input.

        Args:
            mapping (Mapping): dict/mapping containing inputs for VenvCreator

        Returns:
            iterator where each item is a VenvCreator. Creates multiple
            instances when input `path` contains >1 path.
        """
        raw_dirs = mapping.get('path')

        if not raw_dirs:
            raise ContextError(
                "path is mandatory on mapping input for venv create.")

        if not isinstance(raw_dirs, (Sequence, set)):
            raise ContextError(
                "venv.path input should be a string or list. "
                + f"Current input is: {raw_dirs}")

        dirs = ([raw_dirs] if isinstance(
            raw_dirs, SIMPLE_INPUT_TYPE) else raw_dirs)

        system_site_packages = mapping.get('system_site_packages', False)
        clear = mapping.get('clear', False)
        symlinks = mapping.get('symlinks')
        upgrade = mapping.get('upgrade', False)
        with_pip = mapping.get('with_pip', True)
        prompt = mapping.get('prompt')
        upgrade_pip = mapping.get('upgrade_pip', True)
        pip_extras = mapping.get('pip')
        is_quiet = mapping.get('quiet', False)

        for path in dirs:
            yield cls(path=path,
                      pip_extras=pip_extras,
                      system_site_packages=system_site_packages,
                      clear=clear,
                      symlinks=symlinks,
                      upgrade=upgrade,
                      with_pip=with_pip,
                      prompt=prompt,
                      upgrade_pip=upgrade_pip,
                      is_quiet=is_quiet)


class EnvBuilderWithExtraDeps(EnvBuilder):
    """Derived stdlib EnvBuilder to persist in-flight context."""

    def __init__(self, **kwargs):
        """Initialize with special is_quiet flag."""
        self.is_quiet: bool = kwargs.pop('is_quiet', False)
        # the base ctor still does the actual work
        if IS_BEFORE_PY_3_9:
            # upgrade_deps only arrived in python 3.9
            self.upgrade_deps = kwargs.pop('upgrade_deps', False)

        super().__init__(**kwargs)

    def pip_install_extras(self, pip_args: str) -> None:
        """Run python -m pip install {pip_args} in venv.

        You can ONLY call this AFTER post_setup() has run, which in practice
        means you have to have called create().
        """
        logger.debug("installing extra dependencies for path %s",
                     self.context.env_dir)

        cmd = [self.context.env_exec_cmd, '-m', 'pip', 'install']
        if self.is_quiet:
            cmd.append('-q')

        # if input is a list already, no need to shlex split
        shlexed_deps = shlex.split(pip_args) if isinstance(pip_args,
                                                           str) else pip_args

        # each arg could contain a path, thus run expand on all args
        for i, v in enumerate(shlexed_deps):
            shlexed_deps[i] = os.path.expanduser(v)

        cmd.extend(shlexed_deps)

        logger.debug("running %s", cmd)
        subprocess.run(cmd, check=True)

        logger.debug("done")

    def post_setup(self, context: SimpleNamespace) -> None:
        """Save context - this is only way to get at it."""
        logger.debug("started - saving EnvBuilder context...")
        # the alternative to doing this is to override create(), which is
        # gnarly with a lot of logic, so rather not mess with it for
        # maintainability's sake.
        self.context = context
        logger.debug("done")

    def upgrade_dependencies(self, context: SimpleNamespace) -> None:
        """Upgrade pip & setuptools, with quiet switch added if specified."""
        logger.debug('Upgrading %s packages in %s',
                     CORE_VENV_DEPS,
                     context.bin_path)
        cmd = [context.env_exec_cmd, '-m', 'pip', 'install', '--upgrade']

        # this override is identical to base except for this quiet switch
        if self.is_quiet:
            cmd.append('-q')

        cmd.extend(CORE_VENV_DEPS)
        subprocess.check_call(cmd)
