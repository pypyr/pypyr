"""Create a standard python venv using the stdlib venv module."""
import logging

from pypyr.steps.dsl.venv import VenvCreatorStep

logger = logging.getLogger(__name__)


def run_step(context):
    """Create a stdlib venv.

    Args:
        context (pypyr.context.Context): Context must contain
            venv: path

            or

            venv:
                - path1
                - path2

            or

            venv:
                path: path1
                pip: dep1 dep2 -e dep3

            or

            venv:
                path:
                    - path1
                    - path2
                pip: dep1 dep2 -e dep3

            or you can mix simple string and extended mapping syntax:

            venv:
                - path1

                - path: path2
                  pip: dep1 dep2

                - path:
                    - ./path3
                    - /path4
                  pip: dep3 dep4
    """
    logger.debug("started")
    VenvCreatorStep.from_context(context).run_step()
    logger.debug("done")
