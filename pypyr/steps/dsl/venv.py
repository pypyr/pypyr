"""pypyr venv step yaml definition classes - domain specific language."""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
import logging

from pypyr.context import Context
from pypyr.errors import ContextError, MultiError
from pypyr.venv import VenvCreator, SIMPLE_INPUT_TYPE

logger = logging.getLogger(__name__)

EXCEPTION_INPUT = """venv input is wrong. Your input is {bad_type}.
It should be either:

venv: ./path/mydir

OR to specify non-default options (expanded syntax):
venv:
  path: ./path/mydir
  pip: package1 package2
  clear: True

OR to create multiple venvs with default options:
venv:
  - ./path1/dir1
  - /path2/dir3

(Each list item can be a simple string or a mapping in expanded syntax.)

OR to create multiple venvs with the same non-default options:
venv:
  path:
    - ./path1/dir1
    - /path2/dir2
  pip: package1 package2
  clear: True"""

EXCEPTION_LIST_INPUT = """venv list input is wrong. Your input is {bad_type}.
Each list item should be a simple string or a mapping.

venv:
  - ./path1/dir1
  - /path2/dir3

OR to specify non-default options in expanded syntax:
venv:
  - path: ./path1/dir1
    pip: package1 package2
    clear: True

  - path: /path2/dir2
    pip: package3 package4

OR you can mix simple strings for default options and mappings for non-default:
venv:
  - ./path1/dir1

  - path: ./path2/dir2
    pip: package1 package2
    clear: True
"""


class VenvCreatorStep():
    """Model the venv create built-in step and do the actual creation work."""

    CONFIG_KEY = 'venv'

    def __init__(self, venvs: list[VenvCreator]):
        """Initialize step."""
        self.venvs: list[VenvCreator] = venvs

    @classmethod
    def from_context(cls, context: Context) -> VenvCreatorStep:
        """Initialize step from context using this factory."""
        context.assert_key_has_value(key=VenvCreatorStep.CONFIG_KEY,
                                     caller='pypyr.steps.venv')

        venv_config = context.get_formatted(VenvCreatorStep.CONFIG_KEY)

        venvs = []
        if isinstance(venv_config, SIMPLE_INPUT_TYPE):
            venvs.append(VenvCreator(venv_config))
        elif isinstance(venv_config, Mapping):
            venvs.extend(VenvCreator.from_mapping(venv_config))
        elif isinstance(venv_config, Sequence):
            for venv in venv_config:
                if isinstance(venv, SIMPLE_INPUT_TYPE):
                    venvs.append(VenvCreator(venv))
                elif isinstance(venv, Mapping):
                    venvs.extend(VenvCreator.from_mapping(venv))
                else:
                    raise ContextError(
                        EXCEPTION_LIST_INPUT.format(
                            bad_type=type(venv).__name__))
        else:
            raise ContextError(
                EXCEPTION_INPUT.format(bad_type=type(venv_config).__name__))

        return cls(venvs)

    def run_step(self) -> None:
        """Create the venvs when the step runs."""
        logger.debug("started")

        with ThreadPoolExecutor() as executor:
            for venv in self.venvs:
                venv.create_in_executor(executor)

        logger.debug("venv creation threadpool joined...checking results")
        # after all the venv creation is done, can install pip deps
        # pip shouldn't run in parallel, there be dragons.
        errors: list[Exception] = []
        for venv in self.venvs:
            result = venv.check_result()
            # if result contains anything it's an exception
            if result:
                logger.error("venv creation failed for %s with %s",
                             venv.path, result)
                errors.append(result)
            else:
                # install pip deps only if env created successfully
                try:
                    if venv.with_pip:
                        venv.install_dependencies()
                    else:
                        logger.debug(
                            "Not installing any extra dependencies because "
                            + "with_pip is False for %s.", venv.path)

                    logger.info("created venv %s", venv.path)
                except Exception as ex:
                    logger.error("failed installing dependencies to venv %s",
                                 venv.path)
                    errors.append(ex)

        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise MultiError("venvs creation failed:", errors)

        logger.debug("done")
