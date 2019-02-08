"""pypyr step saves the current local datetime to context."""
from datetime import datetime
from dateutil.tz import tzlocal
import logging

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """pypyr step saves current local datetime to context.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key is optional:
                - nowIn. str. Datetime formatting expression. For full list of
                  possible expressions, check here:
                  https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior

    All inputs support pypyr formatting expressions.

    This step creates now in context, containing a string representation of the
    timestamp. If input formatting not specified, defaults to ISO8601.

    Default is:
    YYYY-MM-DDTHH:MM:SS.ffffff, or, if microsecond is 0, YYYY-MM-DDTHH:MM:SS

    Returns:
        None. updates context arg.

    """
    logger.debug("started")

    format_expression = context.get('nowIn', None)

    if format_expression:
        formatted_expression = context.get_formatted_string(format_expression)
        context['now'] = datetime.now(tzlocal()).strftime(formatted_expression)
    else:
        context['now'] = datetime.now(tzlocal()).isoformat()

    logger.info(f"timestamp {context['now']} saved to context now")
    logger.debug("done")
