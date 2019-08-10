"""Smoke test step that adds one to counter."""


def run_step(context):
    context['counter'] = context['counter'] + 1
