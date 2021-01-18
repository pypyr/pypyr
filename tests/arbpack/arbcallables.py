"""Arbitrary callables for testing."""


class ArbCallable():
    """Arb callable test class."""

    def __init__(self, ctorarg):
        """Arbitrary ctor."""
        self.ctorarg = ctorarg

    def __call__(self, arg1):
        """Make it callable."""
        return f'from callable: {self.ctorarg} {arg1}'
