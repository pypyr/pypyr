"""Smoke test step that adds one to counter."""


def run_step(context):
    """Increment counter inside step."""
    context['counter'] = context['counter'] + 1
