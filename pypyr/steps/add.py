"""pypyr step that adds items to a set."""
import logging

from pypyr.utils.asserts import assert_key_exists, assert_key_is_truthy

logger = logging.getLogger(__name__)


def run_step(context):
    """Add item(s) to a set.

    Expects input:
        add:
            set (set or str): Add addMe to this set.
            addMe (any): Add this item to set.
            unpack (bool): Optional. Defaults False. If True, enumerate addMe
                and add each item individually.

    If add.set is a str, it refers to a key in context which contains a
    set, e.g context['my_set'] = {1, 2, 3}. If no such key exists, will create
    a set with that name and add addMe as the 1st item on the new set.

    If you want to add/append to a list, use pypyr.steps.append instead.

    If addMe is enumerable and you want to add its children individually, set
    add.unpack = True.

    Args:
        context (pypyr.context.Context): Mandatory. Context is dict-like.
            Context must contain key 'add'
    """
    logger.debug("started")

    context.assert_key_has_value(key='add', caller=__name__)

    step_input = context.get_formatted('add')

    assert_key_is_truthy(obj=step_input,
                         key='set',
                         caller=__name__,
                         parent='add')

    assert_key_exists(obj=step_input,
                      key='addMe',
                      caller=__name__,
                      parent='add')

    the_set = step_input['set']
    add_me = step_input['addMe']
    is_update = step_input.get('unpack', None)

    # default to unpack/update for lists specifically
    # no real reason other than sort of feels like expected
    # behavior from a pipeline perspective.
    if is_update is None:
        is_update = isinstance(add_me, list)

    # str value means referring to a key in context rather than set instance
    if isinstance(the_set, str):
        existing_set = context.get(the_set, None)

        if existing_set:
            add_or_update_set(existing_set, add_me, is_update)
        else:
            # {x} works only f x single hashable, set(x) when x iterable
            context[the_set] = set(add_me) if is_update else {add_me}
    else:
        add_or_update_set(the_set, add_me, is_update)

    logger.debug("done")


def add_or_update_set(the_set, add_me, is_update):
    """Add or update the set.

    Args:
        the_set (set): The set to add/update
        add_me (any): Item(s) to add to the_set
        is_update (bool): If True does update rather than add.

    Returns: None
    """
    if is_update:
        the_set.update(add_me)
    else:
        the_set.add(add_me)
