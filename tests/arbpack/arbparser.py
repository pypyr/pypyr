"""Test custom parser which returns directly the same thing that was passed."""


def get_parsed_context(context_arg):
    return {'parsed_context': context_arg}
