"""Step that asserts something is true or equal to something else."""
import logging
from pypyr.errors import KeyNotInContextError
from pypyr.utils.types import cast_to_bool

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Assert that something is True or equal to something else.

    Args:
        context (pypyr.context.Context): context is mandatory.
        Uses the following context keys in context:
            - assert
                - this (any): mandatory. If assert['equals'] not specified,
                  eval as boolean.
                - equals (any): optional. Any type.

    Takes one of three input forms:
        assert: evaluate me

        or

        assert:
            this: evaluate me

        or

        assert:
            this: compare me
            equals: to this

    If context['assert'] is not a dict, evaluate contents as bool.
    If context['assert'] is a dict:
        - If context['assert']['this'] evaluates to False raises error.
        - If context['assert']['equals'] exists, raises error if assert.this
          != assert.equals.

    All input forms support string substitutions.

    Returns:
        None

    Raises:
        AssertionError: if assert evaluates to False.

    """
    logger.debug("started")
    assert context, f"context must have value for {__name__}"

    context.assert_key_exists('assert', __name__)

    assert_context = context.get_formatted('assert')

    is_equals_there = False
    is_this_there = False
    if isinstance(assert_context, dict):
        is_this_there = 'this' in assert_context
        if is_this_there:
            assert_this = assert_context['this']
        else:
            assert_this = assert_context

        is_equals_there = 'equals' in assert_context
        if is_equals_there:
            if not is_this_there:
                raise KeyNotInContextError(
                    "you have to set assert.this to use assert.equals.")
            assert_equals = assert_context['equals']
            # compare assertThis to assertEquals
            logger.debug("comparing assert['this'] to assert['equals'].")
            assert_result = (assert_this == assert_equals)
        else:
            # nothing to compare means treat assert or assert.this as a bool.
            if is_this_there:
                logger.debug("evaluating assert['this'] as a boolean.")
            else:
                logger.debug("assert is a dict but contains no `this`. "
                             "evaluating assert value as a boolean.")
            assert_result = cast_to_bool(assert_this)
    else:
        # assert key has a non-dict value so eval directly as a bool.
        logger.debug("evaluating assert value as a boolean.")
        assert_result = cast_to_bool(assert_context)

    logger.info("assert evaluated to %s", assert_result)

    if not assert_result:
        if is_equals_there:
            # emit type to help user, but not the actual field contents.
            type_this = type(assert_this).__name__
            type_equals = type(assert_equals).__name__
            error_text = (
                f"assert assert['this'] is of type {type_this} "
                f"and does not equal assert['equals'] of type {type_equals}.")
        else:
            og_assert = (context['assert']['this']
                         if is_this_there else context['assert'])
            # original literal hard-coded in pipe, so presumably not a
            # sensitive value.
            error_text = (
                f"assert {og_assert} evaluated to False.")
        raise AssertionError(error_text)

    logger.debug("done")
