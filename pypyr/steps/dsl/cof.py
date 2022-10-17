"""pypyr step yaml definition for control of flow instructions."""
from __future__ import annotations
import logging
from collections.abc import Mapping

from pypyr.context import Context
from pypyr.errors import (Call,
                          ContextError,
                          ControlOfFlowInstruction,
                          KeyInContextHasNoValueError,
                          KeyNotInContextError)

SWITCH_KEY = 'switch'

sentinel = object()


def instruction_from_dict(config: Mapping,
                          name: str,
                          instruction_type: type[ControlOfFlowInstruction],
                          context_key: str,
                          original_config: tuple[str, Mapping]
                          ) -> ControlOfFlowInstruction:
    """Create a Call or Jump from input dict."""
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

    return instruction_type(groups=groups,
                            success_group=success_group,
                            failure_group=failure_group,
                            original_config=original_config)


def control_of_flow_instruction(
        name: str,
        instruction_type: type[ControlOfFlowInstruction],
        context: Context,
        context_key: str) -> None:
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
    original_config = (context_key, context[context_key])

    config = context.get_formatted(context_key)

    cof_instruction = instruction_from_dict(config=config,
                                            name=name,
                                            instruction_type=instruction_type,
                                            context_key=context_key,
                                            original_config=original_config)

    logger.info(
        ("step %s about to hand over control with %s: Will run groups: %s "
         " with success %s and failure %s"),
        name,
        context_key,
        cof_instruction.groups,
        cof_instruction.success_group,
        cof_instruction.failure_group)
    raise cof_instruction


def switch(context: Context, name: str) -> None:
    """Run a call instruction from switch where case applies.

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

    Args:
        context: pypyr.context.Context: input context
        name: name of calling step. Very like `pypyr.steps.switch`.
    """
    # this way, logs output as the calling step, which makes more sense
    # to end-user than a mystery steps.dsl.blah logging output.
    logger = logging.getLogger(name)
    logger.debug("starting")

    context.assert_key_has_value(key=SWITCH_KEY, caller=name)

    switch_config = context[SWITCH_KEY]
    # allows runtime to reset switch input when nested switches
    original_config = (SWITCH_KEY, switch_config)

    last_index = len(switch_config) - 1
    cof_instruction = None
    raw_call = None
    is_default = False
    case_expression = False

    for i, case in enumerate(switch_config):
        logger.debug("evaluating case %s", case)
        if i == last_index:
            # last one might be default
            default_case = case.get('default')

            # this is default on the last case in the list
            is_default = default_case is not None

        if is_default:
            logger.debug("no switch case True. running default...")
            raw_call = default_case
        else:
            # `case` could be None or ''.
            raw_expression = case.get('case', sentinel)

            if raw_expression is sentinel:
                raise KeyNotInContextError(
                    f"'case' not found in `switch` index {i}.")

            try:
                # `call` must exist
                raw_call = case['call']
            except KeyError as err:
                raise KeyNotInContextError(
                    f"'call' not found in `switch` index {i}.") from err

            # `call` must have a value
            if not raw_call:
                raise KeyInContextHasNoValueError(
                    f"'call' does not have a value at `switch` index {i}.")

            case_expression = context.get_formatted_as_type(raw_expression,
                                                            out_type=bool)
            if case_expression:
                logger.debug("case %s is True. running `call` group...",
                             raw_expression)

        if case_expression or is_default:
            # only doing expensive format if case True.
            cof_instruction = instruction_from_dict(
                context.get_formatted_value(raw_call),
                name=name,
                instruction_type=Call,
                context_key=SWITCH_KEY,
                original_config=original_config)
            break

    if cof_instruction:
        logger.info(
            ("step %s about to hand over control: Will call groups: %s "
             " with success %s and failure %s"),
            name,
            cof_instruction.groups,
            cof_instruction.success_group,
            cof_instruction.failure_group)
        raise cof_instruction
    else:
        logger.info("no matching case found in switch.")
        logger.debug("done")
