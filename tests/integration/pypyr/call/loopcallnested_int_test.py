"""Nested calls inside loops. These pipelines are in ./tests/pipelines/."""
from pypyr import pipelinerunner
from tests.common.utils import read_file_to_list

expected_file_name = '{0}_expected_output.txt'


def test_pipeline_nested():
    """Nested call control-of-flow works."""
    out = pipelinerunner.run('tests/pipelines/call/nested')

    assert out == {'out': [
        'begin',
        'A',
        'B',
        'C',
        'D',
        'end D',
        'end C',
        'end B',
        'end A',
        'end.'
    ]}

# region for


def test_pipeline_nested_for():
    """Nested call control-of-flow works with for loop."""
    out = pipelinerunner.run('tests/pipelines/call/nestedfor')

    assert out['out'] == [
        'begin',
        'sg1.1',
        'sg2.a',
        'sg2.b',
        'sg2.c',
        'sg1.2',
        'sg2.a',
        'sg2.b',
        'sg2.c',
        'sg1.3',
        'sg2.a',
        'sg2.b',
        'sg2.c',
        'end'
    ]


def test_pipeline_nested_for_deep():
    """Deep nested call control-of-flow works with for loop."""
    pipename = 'tests/pipelines/call/nestedfordeep'
    out = pipelinerunner.run('tests/pipelines/call/nestedfordeep')

    assert out['out'] == read_file_to_list(expected_file_name.format(pipename))


def test_pipeline_nested_for_groups_from_iterators():
    """Nested call control-of-flow works with groups set from iterators."""
    out = pipelinerunner.run(
        'tests/pipelines/call/nestedforgroupsfromiterator')

    assert out['out'] == [
        'begin',
        'sg1.1',
        'A: a',
        'B: b',
        'C: c',
        'end SG1',
        'sg1.2',
        'A: a',
        'B: b',
        'C: c',
        'end SG1',
        'sg1.3',
        'A: a',
        'B: b',
        'C: c',
        'end SG1',
        'end'
    ]


def test_pipeline_nested_for_formatted_groups():
    """Nested call control-of-flow works with groups set dynamically."""
    out = pipelinerunner.run('tests/pipelines/call/nestedforformatted')

    assert out['out'] == [
        'begin',
        'sg1.1',
        'sg2.a',
        'sg2.b',
        'sg2.c',
        'sg1.2',
        'gr2==end',
        'gr2==end',
        'gr2==end',
        'sg1.3',
        'gr2==end',
        'gr2==end',
        'gr2==end',
        'end'
    ]

# endregion for

# region while


def test_pipeline_nested_while():
    """Nested call control-of-flow works with while loop."""
    out = pipelinerunner.run('tests/pipelines/call/nestedwhile')

    assert out['out'] == [
        'begin',
        'sg1.1',
        'sg2.1',
        'sg2.2',
        'sg2.3',
        'sg1.2',
        'sg2.1',
        'sg2.2',
        'sg2.3',
        'sg1.3',
        'sg2.1',
        'sg2.2',
        'sg2.3',
        'end'
    ]


def test_pipeline_nested_while_swallow():
    """Nested call control-of-flow works with while loop swallowing errors."""
    out = pipelinerunner.run('tests/pipelines/call/nestedwhileswallow')

    assert out['out'] == [
        'begin',
        'sg1.1',
        'sg2.1',
        'sg2.2',
        'sg2.3',
        'sg1.2',
        'sg2.1',
        'sg2.2',
        'sg2.3',
        'sg1.3',
        'sg2.1',
        'sg2.2',
        'sg2.3',
        'end'
    ]


def test_pipeline_nested_while_for():
    """Nested call control-of-flow works with while loop AND foreach."""
    pipename = 'tests/pipelines/call/nestedwhilefor'

    out = pipelinerunner.run(pipename)
    assert out['out'] == read_file_to_list(expected_file_name.format(pipename))


def test_pipeline_nested_while_for_retry():
    """Nested call control-of-flow works with while AND foreach AND retry."""
    pipename = 'tests/pipelines/call/nestedwhileforretry'
    out = pipelinerunner.run(pipename)
    assert out['out'] == read_file_to_list(expected_file_name.format(pipename))

# endregion while

# region retries


def test_pipeline_nested_retries():
    """Nested call control-of-flow works with retry loop."""
    out = pipelinerunner.run('tests/pipelines/call/nestedretries')

    assert out['out'] == [
        'begin',
        'sg1.1',
        'sg2.1',
        'sg1.2',
        'sg2.1',
        'sg1.3',
        'sg2.1',
        'no err on sg1.3 Retry counter because of nesting is 1',
        'outer retry counter = 3',
        'end'
    ]
# endregion retries
