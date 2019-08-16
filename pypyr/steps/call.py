"""Control of flow instruction to call another step-group."""
import logging
from pypyr.errors import Call
from pypyr.steps.dsl.cof import control_of_flow_instruction

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Control of flow instruction to call another step-group.

    Call hands control back to this step upon completion, so execution
    continues from this point on-ward.

    Args:
        context: pypyr.context.Context

    Context expexts the following keys:
        call: str. Single group-name to run.

    OR

        call:
            groups: list of str, or str. Single group or list of groups to run.
            success: str. Name of group to run on success completion of groups.
            failure: str. Name of group to run on something going wrong.

    Return:
        None.
    """
    logger.debug("started")

    control_of_flow_instruction(name=__name__,
                                instruction_type=Call,
                                context=context,
                                context_key='call')
