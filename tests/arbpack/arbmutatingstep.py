"""Smoke test step that mutates context."""


def run_step(context):
    context['inside_step'] = 'arb'
