"""Arbitrary testing step that adds arb_in to out list in context."""


def run_step(context):
    """Add arb_in to out.."""
    context['out'].append(context['arb_in'])
