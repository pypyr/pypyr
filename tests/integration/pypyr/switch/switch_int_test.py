"""Nested calls inside loops. These pipelines are in ./tests/pipelines/."""
from pypyr import pipelinerunner


def test_switch_nested():
    """Nested switch control-of-flow works."""
    out = pipelinerunner.run('tests/pipelines/switch/nested')

    assert out == {'out': [
        'begin',
        'A.1',
        'B',
        'A.2',
        'C',
        'A.3',
        'end.'
    ]}
