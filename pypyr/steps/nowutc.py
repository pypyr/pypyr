"""pypyr step saves the current utc datetime to context."""
from datetime import datetime, timezone
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Save current utc datetime to context.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key is optional:
                - nowUtcIn. str. Datetime formatting expression. For full list
                  of possible expressions, check here:
                  https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior

    All inputs support pypyr formatting expressions.

    This step creates now in context, containing a string representation of the
    timestamp. If input formatting not specified, defaults to ISO8601.

    Default is:
    YYYY-MM-DDTHH:MM:SS.ffffff+00:00, or, if microsecond is 0,
    YYYY-MM-DDTHH:MM:SS

    Returns:
        None. updates context arg.

    """
    logger.debug("started")

    format_expression = context.get_formatted_value(context.get('nowUtcIn',
                                                                None))

    if format_expression:
        context['nowUtc'] = datetime.now(
            timezone.utc).strftime(format_expression)
    else:
        context['nowUtc'] = datetime.now(timezone.utc).isoformat()

    logger.info("timestamp %s saved to context nowUtc", context['nowUtc'])
    logger.debug("done")
