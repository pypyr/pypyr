"""pypyr retry back-off strategies.

If you add a back-off strategy, be sure to add it also to the builtin_backoffs
attribute at the bottom.

Attributes:
    builtin_backoffs: dict mapping back-off name to implementation class.
"""
import abc
from collections import deque
import random


# region backoff base
class BackoffBase(abc.ABC):
    """Derive from me for a custom back-off strategy.

    Attributes:
        sleep (float): initial sleep interval in seconds.
        max_sleep (float): upper bound for sleep interval calculation.
        jrc (float): Jitter Range Coefficient.
        kwargs (dict): arbitrary keyword args for use in deriving classes.
    """

    def __init__(self, sleep=1, max_sleep=None, jrc=0, kwargs=None):
        """Initialize back-off strategy.

        Args:
            sleep (float): positive sleep interval in seconds.
            max_sleep (float): upper bound for sleep interval calculation.
            jrc (float): jitter randomizes between [sleep*jrc] and [sleep].
            kwargs (dict): arbitrary arguments for use by deriving classes.
        """
        self.sleep = sleep
        self.max_sleep = max_sleep
        self.jrc = jrc
        self.kwargs = kwargs

    @abc.abstractmethod
    def __call__(self, n):
        """Implement back-off sleep interval calculation here.

        Args:
            n (int): The iteration counter.

        Returns:
            Float. The sleep interval for iteration n.
        """
        raise NotImplementedError()  # pragma: no cover

    def min(self, sleep):
        """Return the smaller of sleep vs max_sleep."""
        max_sleep = self.max_sleep
        return min(sleep, max_sleep) if max_sleep else sleep

    def randomize(self, sleep):
        """Get random number in between (jrc*sleep) and (sleep).

        Does NOT guard against result < max_sleep. This is on purpose.
        It allows you to jitter under or over the sleep interval depending on
        if jrc > 1.
        """
        return random.uniform(sleep * self.jrc, sleep)

# endregion backoff base

# region backoff strategies implementation


class fixed(BackoffBase):
    """Fixed backoff interval(s).

    Sleep can be a single fixed interval, or a list with sleep intervals.

    In the case of a list, each retry iteration will use the next value in the
    list as the back-off interval, until it reaches the last item, which will
    repeat indefinitely.
    """

    def __init__(self, sleep, max_sleep=None, jrc=0, kwargs=None):
        """Initialize the fixed back-off strategy."""
        super().__init__(sleep, max_sleep, jrc, kwargs)
        if isinstance(sleep, (list, set)):
            self.queue = deque(sleep, len(sleep))
            self.fixed_sleep = self.min(self.queue[-1])
        else:
            self.queue = None
            self.fixed_sleep = self.min(sleep)

    def __call__(self, n):
        """Return the fixed backoff interval or the next item on list."""
        if self.queue:
            return self.min(self.queue.popleft())

        return self.fixed_sleep


class jitter(fixed):
    """Add jitter over fixed."""

    def __call__(self, n):
        """Randomize the fixed backoff interval."""
        return self.randomize(super().__call__(n))


class linear(BackoffBase):
    """Backoff increases linearly - the product of iteration and sleep."""

    def __call__(self, n):
        """Return the product of n * sleep."""
        return self.min(n * self.sleep)


class linearjitter(linear):
    """Add jitter over linear."""

    def __call__(self, n):
        """Randomize the product of n * sleep."""
        return self.randomize(super().__call__(n))


class exponential(BackoffBase):
    """Backoff with exponential growth of the sleep coefficient."""

    def __init__(self, sleep=1, max_sleep=None, jrc=0, kwargs=None):
        """Initialize the fixed back-off strategy."""
        super().__init__(sleep, max_sleep, jrc, kwargs)
        self.base = kwargs.get('base', 2) if kwargs else 2

    def __call__(self, n):
        """Return (base**n)*sleep."""
        return self.min(pow(self.base, n) * self.sleep)


class exponentialjitter(exponential):
    """Add jitter over exponential."""

    def __call__(self, n):
        """Randomize exponential result of n."""
        return self.randomize(super().__call__(n))

# endregion backoff strategies implementation


builtin_backoffs = {
    'fixed': fixed,
    'jitter': jitter,
    'linear': linear,
    'linearjitter': linearjitter,
    'exponential': exponential,
    'exponentialjitter': exponentialjitter
}
