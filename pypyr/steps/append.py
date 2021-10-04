"""pypyr step that appends items to a mutable sequence, such as a list."""
import logging

from pypyr.utils.asserts import assert_key_exists, assert_key_is_truthy

logger = logging.getLogger(__name__)


def run_step(context):
    """Append item to a mutable sequence.

    Expects input:
        append:
            list (list or str): Add addMe to this mutable sequence.
            addMe (any): Add this item to the list.
            unpack (bool): Optional. Defaults False. If True, enumerate addMe
                and append each item individually.

    If append.list is a str, it refers to a key in context which contains a
    list, e.g context['my_list'] = [1, 2, 3]. If no such key exists, will
    create a list with that name and add addMe as the 1st item on the new list.

    This is an append, not an extend, unless append.unpack = True.

    If you want to add to a set, use pypyr.steps.add instead.

    Args:
        context (pypyr.context.Context): Mandatory. Context is a dictionary or
            dictionary-like.
            Context must contain key 'append'
    """
    logger.debug("started")

    context.assert_key_has_value(key='append', caller=__name__)

    step_input = context.get_formatted('append')

    assert_key_is_truthy(obj=step_input,
                         key='list',
                         caller=__name__,
                         parent='append')

    assert_key_exists(obj=step_input,
                      key='addMe',
                      caller=__name__,
                      parent='append')

    lst = step_input['list']
    add_me = step_input['addMe']
    is_extend = step_input.get('unpack', False)

    # str value means referring to a key in context rather than list instance
    if isinstance(lst, str):
        existing_sequence = context.get(lst, None)

        if existing_sequence:
            append_or_extend_list(existing_sequence, add_me, is_extend)
        else:
            # list(x) works only if x is iterable, [x] works when x != iterable
            context[lst] = list(add_me) if is_extend else [add_me]
    else:
        # anything that supports append: list, deque, array... if not is_extend
        append_or_extend_list(lst, add_me, is_extend)

    logger.debug("started")


def append_or_extend_list(lst, add_me, is_extend):
    """Append or extend list.

    Args:
        lst (list-like): The list to append/extend
        add_me (any): Item(s) to append/extend to lst
        is_extend (bool): If True does extend rather than append.

    Returns: None
    """
    if is_extend:
        lst.extend(add_me)
    else:
        lst.append(add_me)
