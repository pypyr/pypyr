"""Smoke test step that mutates context."""


def run_step(context):
    """Mutate context inside step."""
    context['inside_step'] = 'arb'
