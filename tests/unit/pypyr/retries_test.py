"""retries.py unit tests."""
import inspect
from unittest.mock import call, patch
import pypyr.retries

# region BackoffBase


class ArbTestBackoff(pypyr.retries.BackoffBase):
    """Test backoff derivation."""

    def __call__(self, n):
        """Just return n."""
        return n


def test_backoffbase_ctor_defaults():
    """Backoff Base instantiates with defaults."""
    b = ArbTestBackoff()
    assert b.sleep == 1
    assert b.max_sleep is None
    assert b.jrc == 0
    assert b.kwargs is None
    assert b(123) == 123


def test_backoffbase_ctor_all():
    """Backoff Base instantiates with all values."""
    b = ArbTestBackoff(sleep=123, max_sleep=456, jrc=789, kwargs={'a': 'b'})
    assert b.sleep == 123
    assert b.max_sleep == 456
    assert b.jrc == 789
    assert b.kwargs == {'a': 'b'}
    assert b(123) == 123


def test_backoffbase_min_none():
    """Min when max_sleep None."""
    b = ArbTestBackoff()
    assert b.min(1) == 1
    assert b.min(4) == 4


def test_backoffbase_min():
    """Min with value for max_sleep."""
    b = ArbTestBackoff(max_sleep=3)
    assert b.min(1) == 1
    assert b.min(4) == 3


@patch('pypyr.retries.random.uniform', return_value=123)
def test_backoffbase_randomize(mock_random):
    """Randomize uses product of jrc and sleep as one side bound for random."""
    b = ArbTestBackoff(jrc=0.5)
    assert b.randomize(3) == 123

    mock_random.assert_called_once_with(1.5, 3)


@patch('pypyr.retries.random.uniform', return_value=123)
def test_backoffbase_randomize_jrc_gt_1(mock_random):
    """Randomize can use jrc > 1."""
    b = ArbTestBackoff(jrc=2)
    assert b.randomize(3) == 123

    mock_random.assert_called_once_with(6, 3)


@patch('pypyr.retries.random.uniform', return_value=123)
def test_backoffbase_randomize_default_0(mock_random):
    """Randomize uses 0 as lower bound by default."""
    b = ArbTestBackoff()
    assert b.randomize(3) == 123

    mock_random.assert_called_once_with(0, 3)

# endregion BackoffBase

# region retry strategies
# region fixed


def test_retries_fixed_with_single():
    """Fixed with single float input."""
    f = pypyr.retries.fixed(sleep=123)
    assert f(0) == 123
    assert f(1) == 123
    assert f(2) == 123


def test_retries_fixed_with_list():
    """Fixed with list input."""
    f = pypyr.retries.fixed(sleep=[2, 4, 6])
    assert f(0) == 2
    assert f(1) == 4
    assert f(2) == 6
    assert f(3) == 6
    assert f(4) == 6
    # arb repeat of n
    assert f(0) == 6


def test_retries_fixed_with_set():
    """Fixed with list input."""
    f = pypyr.retries.fixed(sleep={2, 4, 6})
    assert f(0) == 2
    assert f(1) == 4
    assert f(2) == 6
    assert f(3) == 6
    assert f(4) == 6
    # arb repeat of n
    assert f(0) == 6


def test_retries_fixed_single_with_max():
    """Fixed with single float input works with max."""
    f = pypyr.retries.fixed(sleep=123, max_sleep=456)
    assert f(0) == 123
    assert f(1) == 123
    assert f(2) == 123

    f = pypyr.retries.fixed(sleep=456, max_sleep=321)
    assert f(0) == 321
    assert f(1) == 321
    assert f(2) == 321


def test_retries_fixed_with_list_max():
    """Fixed with list input works with max."""
    f = pypyr.retries.fixed(sleep=[2, 4, 6], max_sleep=4.5)
    assert f(0) == 2
    assert f(1) == 4
    assert f(2) == 4.5
    assert f(3) == 4.5
    assert f(4) == 4.5
    # arb repeat of n
    assert f(0) == 4.5

# endregion fixed

# region jitter


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_single(mock_random):
    """Jitter with single float input."""
    j = pypyr.retries.jitter(sleep=123)
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999

    assert mock_random.mock_calls == [call(0, 123),
                                      call(0, 123),
                                      call(0, 123)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_single_max(mock_random):
    """Jitter with single float input honors max."""
    j = pypyr.retries.jitter(sleep=123, max_sleep=111)
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999

    assert mock_random.mock_calls == [call(0, 111),
                                      call(0, 111),
                                      call(0, 111)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_list(mock_random):
    """Jitter with list of float input."""
    j = pypyr.retries.jitter(sleep=[1, 2, 3])
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999
    assert j(3) == 999
    assert j(4) == 999
    # arb repeat
    assert j(1) == 999

    assert mock_random.mock_calls == [call(0, 1),
                                      call(0, 2),
                                      call(0, 3),
                                      call(0, 3),
                                      call(0, 3),
                                      call(0, 3)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_list_max(mock_random):
    """Jitter with list of float input honors max."""
    j = pypyr.retries.jitter(sleep=[1, 2, 3], max_sleep=2)
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999
    assert j(3) == 999
    assert j(4) == 999
    # arb repeat
    assert j(1) == 999

    assert mock_random.mock_calls == [call(0, 1),
                                      call(0, 2),
                                      call(0, 2),
                                      call(0, 2),
                                      call(0, 2),
                                      call(0, 2)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_single_jrc_down(mock_random):
    """Jitter with single float input and jrc < 1."""
    j = pypyr.retries.jitter(sleep=100, jrc=0.1)
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999

    assert mock_random.mock_calls == [call(10, 100),
                                      call(10, 100),
                                      call(10, 100)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_single_jrc_up(mock_random):
    """Jitter with single float input and jrc > 1."""
    j = pypyr.retries.jitter(sleep=100, jrc=3.5)
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999

    assert mock_random.mock_calls == [call(350, 100),
                                      call(350, 100),
                                      call(350, 100)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_jitter_list_jrc_up_max(mock_random):
    """Jitter with list float input and jrc > 1 ignore max."""
    j = pypyr.retries.jitter(sleep=[100, 200, 300], jrc=2, max_sleep=200)
    assert j(0) == 999
    assert j(1) == 999
    assert j(2) == 999
    assert j(1) == 999

    assert mock_random.mock_calls == [call(200, 100),
                                      call(400, 200),
                                      call(400, 200),
                                      call(400, 200)]
# endregion jitter

# region linear


def test_retries_linear():
    """Linear retry works."""
    lr = pypyr.retries.linear()
    assert lr(0) == 0
    assert lr(1) == 1
    assert lr(2) == 2
    assert lr(3) == 3
    assert lr(1) == 1


def test_retries_linear_with_max():
    """Linear retry works."""
    lr = pypyr.retries.linear(sleep=2, max_sleep=8)
    assert lr(0) == 0
    assert lr(1) == 2
    assert lr(2) == 4
    assert lr(3) == 6
    assert lr(4) == 8
    assert lr(5) == 8
    assert lr(10) == 8
    assert lr(1) == 2

# endregion linear


# region linearjitter

@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_linearjitter(mock_random):
    """Linearjitter linear progression."""
    lj = pypyr.retries.linearjitter(sleep=3)
    assert lj(1) == 999
    assert lj(2) == 999
    assert lj(3) == 999
    assert lj(1) == 999

    assert mock_random.mock_calls == [call(0, 3),
                                      call(0, 6),
                                      call(0, 9),
                                      call(0, 3)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_linearjitter_max(mock_random):
    """Linearjitter linear progression honors max."""
    lj = pypyr.retries.linearjitter(sleep=4, max_sleep=15)
    assert lj(1) == 999
    assert lj(2) == 999
    assert lj(3) == 999
    assert lj(4) == 999
    assert lj(2) == 999

    assert mock_random.mock_calls == [call(0, 4),
                                      call(0, 8),
                                      call(0, 12),
                                      call(0, 15),
                                      call(0, 8)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_linearjitter_jrc_down(mock_random):
    """Linearjitter linear progression with jrc < 1."""
    lj = pypyr.retries.linearjitter(sleep=3, jrc=0.5)
    assert lj(1) == 999
    assert lj(2) == 999
    assert lj(3) == 999
    assert lj(1) == 999

    assert mock_random.mock_calls == [call(1.5, 3),
                                      call(3, 6),
                                      call(4.5, 9),
                                      call(1.5, 3)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_linearjitter_jrc_up(mock_random):
    """Linearjitter linear progression with jrc > 1."""
    lj = pypyr.retries.linearjitter(sleep=3, jrc=2)
    assert lj(1) == 999
    assert lj(2) == 999
    assert lj(3) == 999
    assert lj(1) == 999

    assert mock_random.mock_calls == [call(6, 3),
                                      call(12, 6),
                                      call(18, 9),
                                      call(6, 3)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_linearjitter_jrc_over_max(mock_random):
    """Linearjitter linear progression with jrc > 1 ignores max."""
    lj = pypyr.retries.linearjitter(sleep=3, jrc=2, max_sleep=10)
    assert lj(1) == 999
    assert lj(2) == 999
    assert lj(3) == 999
    assert lj(1) == 999

    assert mock_random.mock_calls == [call(6, 3),
                                      call(12, 6),
                                      call(18, 9),
                                      call(6, 3)]
# endregion linearjitter


# region exponential

def test_retries_exponential():
    """Exponential retry works."""
    e = pypyr.retries.exponential()
    assert e(0) == 1
    assert e(1) == 2
    assert e(2) == 4
    assert e(3) == 8
    assert e(4) == 16
    assert e(1) == 2


def test_retries_exponential_kwargs_no_base():
    """Exponential retry works with kwargs and no base set."""
    e = pypyr.retries.exponential(kwargs={'notbase': 3})
    assert e(0) == 1
    assert e(1) == 2
    assert e(2) == 4
    assert e(3) == 8
    assert e(4) == 16
    assert e(1) == 2


def test_retries_exponential_with_sleep():
    """Exponential retry works with sleep coefficient."""
    e = pypyr.retries.exponential(sleep=2)
    assert e(0) == 2
    assert e(1) == 4
    assert e(2) == 8
    assert e(3) == 16
    assert e(4) == 32
    assert e(1) == 4


def test_retries_exponential_base_3():
    """Exponential retry works with different base."""
    e = pypyr.retries.exponential(kwargs={'base': 3})
    assert e(0) == 1
    assert e(1) == 3
    assert e(2) == 9
    assert e(3) == 27
    assert e(4) == 81
    assert e(1) == 3


def test_retries_exponential_with_max():
    """Exponential retry works with max."""
    e = pypyr.retries.exponential(max_sleep=15)
    assert e(0) == 1
    assert e(1) == 2
    assert e(2) == 4
    assert e(3) == 8
    assert e(4) == 15
    assert e(5) == 15
    assert e(1) == 2

# endregion exponential

# region exponentialjitter


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_exponentialjitter(mock_random):
    """Exponentialjitter retry works."""
    ej = pypyr.retries.exponentialjitter()
    assert ej(0) == 999
    assert ej(1) == 999
    assert ej(2) == 999
    assert ej(3) == 999
    assert ej(4) == 999
    assert ej(1) == 999
    assert ej(8) == 999

    assert mock_random.mock_calls == [call(0, 1),
                                      call(0, 2),
                                      call(0, 4),
                                      call(0, 8),
                                      call(0, 16),
                                      call(0, 2),
                                      call(0, 256)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_exponentialjitter_jrc_down(mock_random):
    """Exponentialjitter retry works with jrc lower range."""
    ej = pypyr.retries.exponentialjitter(jrc=0.5)
    assert ej(0) == 999
    assert ej(1) == 999
    assert ej(2) == 999
    assert ej(3) == 999
    assert ej(4) == 999
    assert ej(1) == 999
    assert ej(8) == 999

    assert mock_random.mock_calls == [call(0.5, 1),
                                      call(1, 2),
                                      call(2, 4),
                                      call(4, 8),
                                      call(8, 16),
                                      call(1, 2),
                                      call(128, 256)]


@patch('pypyr.retries.random.uniform', return_value=999)
def test_retries_exponentialjitter_jrc_up_max(mock_random):
    """Exponentialjitter retry works with jrc upper range."""
    ej = pypyr.retries.exponentialjitter(jrc=2)
    assert ej(0) == 999
    assert ej(1) == 999
    assert ej(2) == 999
    assert ej(3) == 999
    assert ej(4) == 999
    assert ej(1) == 999
    assert ej(8) == 999

    assert mock_random.mock_calls == [call(2, 1),
                                      call(4, 2),
                                      call(8, 4),
                                      call(16, 8),
                                      call(32, 16),
                                      call(4, 2),
                                      call(512, 256)]
# endregion exponentialjitter

# endregion retry strategies


def test_backoff_export_list():
    """The backoff export list should have all BackOffBase children.

    If you've added a new back-off strategy, add it to the look-up dict:
    pypyr.retries.builtin_backoffs.
    """
    members = inspect.getmembers(
        pypyr.retries,
        lambda m: inspect.isclass(m)
        and issubclass(m, pypyr.retries.BackoffBase))

    assert pypyr.retries.builtin_backoffs == {
        n[0]: n[1] for n in members if n[0] != 'BackoffBase'}
