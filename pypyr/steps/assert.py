"""Step that asserts something is true or equal to something else."""
import logging
from pypyr.errors import ContextError

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Assert that something is True or equal to something else.

    Args:
        context: dictionary-like pypyr.context.Context. context is mandatory.
        Uses the following context keys in context:
            - assertThis. mandatory. Any type. If assertEquals not specified,
              evals as boolean.
            - assertEquals. optional. Any type.

    If assertThis evaluates to False raises error.
    If assertEquals is specified, raises error if assertThis != assertEquals.

    assertThis & assertEquals both support string substitutions.

    Returns:
        None

    Raises:
        ContextError: if assert evaluates to False.
    """
    logger.debug("started")
    assert context, f"context must have value for {__name__}"
    context.assert_key_has_value('assertThis', __name__)

    if 'assertEquals' in context:
        # compare assertThis to assertEquals
        logger.debug("comparing assertThis to assertEquals.")
        assert_result = (context.get_formatted('assertThis')
                         ==
                         context.get_formatted('assertEquals'))
    else:
        # nothing to compare means treat assertThis as a bool.
        logger.debug("Evaluating assertThis as a boolean.")
        assert_result = context.get_formatted_as_type(context['assertThis'],
                                                      out_type=bool)

    logger.info(f"assert evaluated to {assert_result}")

    if not assert_result:
        assert_equals = context.get('assertEquals', None)

        if assert_equals is None:
            # if it's a bool it's presumably not a sensitive value.
            error_text = (
                f"assert {context['assertThis']} evaluated to False.")
        else:
            # emit type to help user, but not the actual field contents.
            error_text = (
                f"assert context['assertThis'] is of type "
                f"{type(context.get_formatted('assertThis')).__name__} "
                f"and does not equal context['assertEquals'] of type "
                f"{type(context.get_formatted('assertEquals')).__name__}.")
        raise ContextError(error_text)

    logger.debug("done")
