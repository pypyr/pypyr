"""Control of flow instruction to switch between groups (if-else)."""
import logging
from pypyr.steps.dsl.cof import switch

logger = logging.getLogger(__name__)


def run_step(context):
    """Control of flow instruction to switch between step-groups.

    Call hands control back to this step upon completion, so execution
    continues from this point on-ward when the called groups are done.

    No fallthrough - will run the first matching group and not evaluate any
    case expressions thereafter.

    Args:
        context: pypyr.context.Context

    Context expects the following keys:
        switch:
            - case: expression. exec `call` when expression True.
              call: str. Single group-name to run.

            - default: exec `call` when none of the case expressions True.

    OR

        switch:
            - case: expression. exec call `when` expression True.
              call:
                groups: list[str] | str. Single group or list of groups to run.
                success: str. Name of group to run on success completion.
                failure: str. Name of group to run on something going wrong.

    `default` is optional. If you specify default, it must be the last item in
    the switch list.

    Return:
        None.
    """
    logger.debug("started")

    switch(context=context, name=__name__)

    # this will only run if no case condition true - else switch will kick out
    # of method with a raise.
    logger.debug("done")
