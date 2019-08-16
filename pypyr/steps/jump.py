"""Control of flow instruction to jump to another step-group."""
import logging
from pypyr.errors import Jump
from pypyr.steps.dsl.cof import control_of_flow_instruction

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Control of flow instruction to jump to another step-group.

    Once jumped, you don't come back here.

    Args:
        context: pypyr.context.Context

    Context expexts the following keys:
        jump: str. Single group-name to run.

    OR

        jump:
            groups: list of str, or str. Single group or list of groups to run.
            success: str. Name of group to run on success completion of groups.
            failure: str. Name of group to run on something going wrong.

    Return:
        None.
    """
    logger.debug("started")

    control_of_flow_instruction(name=__name__,
                                instruction_type=Jump,
                                context=context,
                                context_key='jump')
