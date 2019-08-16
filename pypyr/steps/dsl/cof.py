"""pypyr step yaml definition for control of flow instructions."""
import logging
from pypyr.errors import (ContextError,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)


def control_of_flow_instruction(name, instruction_type, context, context_key):
    """Run a control of flow instruction.

    The step config in the context dict looks like this:
        <<instruction-name>>: <<cmd string>>. Mandatory.

        OR, as a dict
        <<instruction-name:
            groups: <<str>> or <<list of str>> - mandatory.
            success: <<str>>
            failure: <<str>>

    Args:
        name: Unique name for step. Likely __name__ of calling step.
        instruction_type: Type - must inherit from
                          pypyr.errors.ControlOfFlowInstruction
        context: pypyr.context.Context. Look for config in this context
                 instance.
        context_key: str name of step config in context.

    """
    assert name, ("name parameter must exist for a ControlOfFlowStep.")
    assert context, ("context param must exist for ControlOfFlowStep.")
    # this way, logs output as the calling step, which makes more sense
    # to end-user than a mystery steps.dsl.blah logging output.
    logger = logging.getLogger(name)
    logger.debug("starting")

    context.assert_key_has_value(key=context_key, caller=name)

    config = context.get_formatted(context_key)

    if isinstance(config, str):
        groups = [config]
        success_group = None
        failure_group = None
    elif isinstance(config, list):
        groups = config
        success_group = None
        failure_group = None
    elif isinstance(config, dict):
        if 'groups' not in config:
            raise KeyNotInContextError(
                f"{context_key} needs a child key 'groups', which should "
                "be a list or a str with the step-group name(s) you want "
                f"to run. This is for step {name}.")
        groups = config['groups']
        if not groups:
            raise KeyInContextHasNoValueError(
                f"{context_key}.groups must have a value for step {name}")

        if isinstance(groups, str):
            groups = [groups]

        success_group = config.get('success', None)
        failure_group = config.get('failure', None)
    else:
        raise ContextError(
            f"{context_key} needs a child key 'groups', which should "
            "be a list or a str with the step-group name(s) you want "
            f"to run. This is for step {name}. Instead, you've got {config}")

    if success_group is not None and not isinstance(success_group, str):
        raise ContextError(
            f"{context_key}.success must be a string for {name}.")

    if failure_group is not None and not isinstance(failure_group, str):
        raise ContextError(
            f"{context_key}.failure must be a string for {name}.")

    logger.info(
        ("step %s about to hand over control with %s: Will run groups: %s "
         " with success %s and failure %s"),
        name,
        context_key,
        groups,
        success_group,
        failure_group)
    raise instruction_type(groups=groups,
                           success_group=success_group,
                           failure_group=failure_group)
