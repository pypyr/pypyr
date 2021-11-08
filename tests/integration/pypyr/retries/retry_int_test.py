"""retry integration tests."""
from pathlib import Path
from unittest.mock import call, patch
from pypyr import pipelinerunner

working_dir_tests = Path(Path.cwd(), 'tests')


@patch('pypyr.retries.random.uniform', return_value=123)
@patch('time.sleep')
def test_retry_with_yaml_anchor(mock_sleep, mock_random):
    """Retry uses common shared anchors."""
    out = pipelinerunner.run(
        pipeline_name='tests/pipelines/retries/retry-anchors',
        dict_in={'outList': []})

    assert out['outList'] == ['s1.1',
                              's1.2',
                              's1.3',
                              's2.1',
                              's2.2',
                              's3.1',
                              's3.2',
                              's3.3']

    assert mock_random.mock_calls == [call(1.5, 3), call(4.25, 8.5)]
    assert mock_sleep.mock_calls == [call(2),
                                     call(4),
                                     call(2),
                                     call(123),
                                     call(123)]
