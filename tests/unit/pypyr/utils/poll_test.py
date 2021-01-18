"""poll.py unit tests."""
import logging
from unittest.mock import call, MagicMock, patch
import pypyr.utils.poll as poll


# region wait_until_true
from tests.common.utils import patch_logger


@patch('time.sleep')
def test_wait_until_true_with_static_decorator(mock_time_sleep):
    """wait_until_true with static decorator."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'expected value',
        'test string 5'
    ]

    @poll.wait_until_true(interval=0.01, max_attempts=10)
    def decorate_me(arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        return mock(arg1) == 'expected value'

    assert decorate_me('v1', 'v2')
    assert mock.call_count == 4
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 3
    mock_time_sleep.assert_called_with(0.01)


@patch('time.sleep')
def test_wait_until_true_invoke_inline(mock_time_sleep):
    """wait_until_true with dynamic invocation."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'expected value',
        'test string 5'
    ]

    def decorate_me(arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        return mock(arg1) == 'expected value'

    assert poll.wait_until_true(interval=0.01, max_attempts=10)(
        decorate_me)('v1', 'v2')
    assert mock.call_count == 4
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 3
    mock_time_sleep.assert_called_with(0.01)


@patch('time.sleep')
def test_wait_until_true_with_timeout(mock_time_sleep):
    """wait_until_true with dynamic invocation, exhaust wait attempts."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'test string 4',
        'test string 5',
        'test string 6',
        'test string 7',
        'test string 8',
        'test string 9',
        'test string 10',
        'test string 11',
    ]

    def decorate_me(arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        return mock(arg1) == 'expected value'

    assert not poll.wait_until_true(interval=0.01, max_attempts=10)(
        decorate_me)('v1', 'v2')
    assert mock.call_count == 10
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 9
    mock_time_sleep.assert_called_with(0.01)


@patch('time.sleep')
def test_wait_until_true_once_not_found(mock_time_sleep):
    """wait_until_true max_attempts 1."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
    ]

    def decorate_me(arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        return mock(arg1) == 'expected value'

    assert not poll.wait_until_true(interval=0.01, max_attempts=1)(
        decorate_me)('v1', 'v2')
    mock.assert_called_once_with('v1')
    mock_time_sleep.assert_not_called()


@patch('time.sleep')
def test_wait_until_true_once_found(mock_time_sleep):
    """wait_until_true max_attempts 1."""
    mock = MagicMock()
    mock.side_effect = [
        'expected value',
        'test string 2',
    ]

    def decorate_me(arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        return mock(arg1) == 'expected value'

    assert poll.wait_until_true(interval=0.01, max_attempts=1)(
        decorate_me)('v1', 'v2')
    mock.assert_called_once_with('v1')
    mock_time_sleep.assert_not_called()

# endregion wait_until_true

# region while_until_true


@patch('time.sleep')
def test_while_until_true_with_static_decorator(mock_time_sleep):
    """while_until_true with static decorator."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'expected value',
        'test string 5'
    ]

    actual_counter = 0

    @poll.while_until_true(interval=0.01, max_attempts=10)
    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        return mock(arg1) == 'expected value'

    # the decorator injects the 1st arg (counter)
    assert decorate_me('v1', 'v2')
    assert mock.call_count == 4
    mock.assert_called_with('v1')
    assert mock_time_sleep.mock_calls == [call(0.01), call(0.01), call(0.01)]


@patch('time.sleep')
def test_while_until_true_invoke_inline(mock_time_sleep):
    """while_until_true with dynamic invocation."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'expected value',
        'test string 5'
    ]

    actual_counter = 0

    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        return mock(arg1) == 'expected value'

    assert poll.while_until_true(interval=0.01, max_attempts=10)(
        decorate_me)('v1', 'v2')
    assert mock.call_count == 4
    mock.assert_called_with('v1')
    assert mock_time_sleep.mock_calls == [call(0.01), call(0.01), call(0.01)]


@patch('time.sleep')
def test_while_until_true_with_exhaust(mock_time_sleep):
    """while_until_true with dynamic invocation, exhaust wait attempts."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'test string 4',
        'test string 5',
        'test string 6',
        'test string 7',
        'test string 8',
        'test string 9',
        'test string 10',
        'test string 11',
    ]

    actual_counter = 0

    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        out = mock(arg1)
        assert out == f'test string {counter}'
        return out == 'expected value'

    assert not poll.while_until_true(interval=0.01, max_attempts=10)(
        decorate_me)('v1', 'v2')
    assert mock.call_count == 10
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 9
    mock_time_sleep.assert_called_with(0.01)


@patch('time.sleep')
def test_while_until_true_once_not_found(mock_time_sleep):
    """while_until_true max_attempts 1."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
    ]

    actual_counter = 0

    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        return mock(arg1) == 'expected value'

    assert not poll.while_until_true(interval=0.01, max_attempts=1)(
        decorate_me)('v1', 'v2')
    mock.assert_called_once_with('v1')
    mock_time_sleep.assert_not_called()


@patch('time.sleep')
def test_while_until_true_once_found(mock_time_sleep):
    """wait_until_true max_attempts 1."""
    mock = MagicMock()
    mock.side_effect = [
        'expected value',
        'test string 2',
    ]

    actual_counter = 0

    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        return mock(arg1) == 'expected value'

    assert poll.while_until_true(interval=0.01, max_attempts=1)(
        decorate_me)('v1', 'v2')
    mock.assert_called_once_with('v1')
    mock_time_sleep.assert_not_called()


@patch('time.sleep')
def test_while_until_true_no_max(mock_time_sleep):
    """while_until_true with dynamic invocation, infinite (max is None)."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
        'test string 4',
        'test string 5',
        'test string 6',
        'test string 7',
        'test string 8',
        'test string 9',
        'test string 10',
        'test string 11',
    ]

    actual_counter = 0

    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        out = mock(arg1)
        assert out == f'test string {counter}'
        return out == 'test string 11'

    with patch_logger('pypyr.utils.poll', logging.DEBUG) as mock_logger_debug:
        assert (poll.while_until_true(interval=0.01,
                                      max_attempts=None)(decorate_me)('v1',
                                                                      'v2'))
    assert mock_logger_debug.mock_calls == [
        call('started'),
        call('Looping every 0.01 seconds.'),
        call('iteration 1. Sleeping for 0.01s. Still waiting...'),
        call('iteration 2. Sleeping for 0.01s. Still waiting...'),
        call('iteration 3. Sleeping for 0.01s. Still waiting...'),
        call('iteration 4. Sleeping for 0.01s. Still waiting...'),
        call('iteration 5. Sleeping for 0.01s. Still waiting...'),
        call('iteration 6. Sleeping for 0.01s. Still waiting...'),
        call('iteration 7. Sleeping for 0.01s. Still waiting...'),
        call('iteration 8. Sleeping for 0.01s. Still waiting...'),
        call('iteration 9. Sleeping for 0.01s. Still waiting...'),
        call('iteration 10. Sleeping for 0.01s. Still waiting...'),
        call('iteration 11. Desired state reached.'),
        call('done')]

    assert mock.call_count == 11
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 10
    mock_time_sleep.assert_called_with(0.01)


@patch('time.sleep')
def test_while_until_true_max_exhaust(mock_time_sleep):
    """while_until_true with dynamic invocation, exhaust max."""
    mock = MagicMock()
    mock.side_effect = [
        'test string 1',
        'test string 2',
        'test string 3',
    ]

    actual_counter = 0

    def decorate_me(counter, arg1, arg2):
        """Test static decorator syntax."""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        nonlocal actual_counter
        actual_counter += 1
        assert actual_counter == counter
        out = mock(arg1)
        assert out == f'test string {counter}'
        return False

    with patch_logger('pypyr.utils.poll', logging.DEBUG) as mock_logger_debug:
        assert not (poll.while_until_true(interval=0.01,
                                          max_attempts=3)(decorate_me)('v1',
                                                                       'v2'))
    assert mock_logger_debug.mock_calls == [
        call('started'),
        call('Looping every 0.01 seconds for 3 attempts'),
        call('iteration 1. Sleeping for 0.01s. Still waiting...'),
        call('iteration 2. Sleeping for 0.01s. Still waiting...'),
        call('iteration 3. Max attempts exhausted.'),
        call('done')]

    assert mock.call_count == 3
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 2
    assert mock_time_sleep.mock_calls == [call(0.01), call(0.01)]


def arb_callable(n):
    """Arb callable for testing."""
    return n * 2


@patch('time.sleep')
def test_while_until_true_callable_with_max_attempts(mock_sleep):
    """Interval calculated from callable per iteration with max set."""
    decorate_me = MagicMock()
    decorate_me.side_effect = [False, False, True, False]

    assert poll.while_until_true(interval=arb_callable,
                                 max_attempts=3)(decorate_me)('arg1', 'arg2')

    assert decorate_me.mock_calls == [call(1, 'arg1', 'arg2'),
                                      call(2, 'arg1', 'arg2'),
                                      call(3, 'arg1', 'arg2')]

    assert mock_sleep.mock_calls == [call(2), call(4)]


@patch('time.sleep')
def test_while_until_true_callable_without_max_attempts(mock_sleep):
    """Interval calculated from callable per iteration infinite."""
    decorate_me = MagicMock()
    decorate_me.side_effect = [False, False, False, True, False]

    assert poll.while_until_true(interval=arb_callable,
                                 max_attempts=None)(decorate_me)('arg1',
                                                                 'arg2')

    assert decorate_me.mock_calls == [call(1, 'arg1', 'arg2'),
                                      call(2, 'arg1', 'arg2'),
                                      call(3, 'arg1', 'arg2'),
                                      call(4, 'arg1', 'arg2')]

    assert mock_sleep.mock_calls == [call(2), call(4), call(6)]
# endregion while_until_true
