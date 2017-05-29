"""poll.py unit tests."""
import pypyr.utils.poll as poll
from unittest.mock import MagicMock, patch


# ----------------- wait_until_true -------------------------------------------
@patch('time.sleep')
def test_wait_until_true_with_static_decorator(mock_time_sleep):
    """wait_until_true with static decorator"""
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
        """Test static decorator syntax"""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        if mock(arg1) == 'expected value':
            return True
        else:
            return False

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
        """Test static decorator syntax"""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        if mock(arg1) == 'expected value':
            return True
        else:
            return False

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
        """Test static decorator syntax"""
        assert arg1 == 'v1'
        assert arg2 == 'v2'
        if mock(arg1) == 'expected value':
            return True
        else:
            return False

    assert not poll.wait_until_true(interval=0.01, max_attempts=10)(
        decorate_me)('v1', 'v2')
    assert mock.call_count == 10
    mock.assert_called_with('v1')
    assert mock_time_sleep.call_count == 10
    mock_time_sleep.assert_called_with(0.01)

# ----------------- wait_until_true -------------------------------------------
