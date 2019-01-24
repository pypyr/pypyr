"""fetchyaml.py unit tests."""
from unittest.mock import mock_open, patch
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fetchyaml as filefetcher
import pytest


def test_fetchyaml_no_path_raises():
    """None path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filefetcher.run_step(context)

    assert str(err_info.value) == ("context['fetchYaml'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fetchyaml.")


def test_fetchyaml_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fetchYaml': {
            'path': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filefetcher.run_step(context)

    assert str(err_info.value) == ("context['fetchYaml']['path'] must have a "
                                   "value for pypyr.steps.fetchyaml.")


def test_fetchyaml_pass():
    """Relative path to yaml should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fetchYaml': {
            'path': './tests/testfiles/dict.yaml'}})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['ok1'] == 'ov1'
    assert context['fetchYaml']['path'] == './tests/testfiles/dict.yaml'
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


def test_fetchyaml_pass_with_substitution():
    """Relative path to yaml should succeed with path substitution.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileName': 'dict',
        'fetchYaml': {
            'path': './tests/testfiles/{fileName}.yaml'}})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['ok1'] == 'ov1'
    assert context['fetchYaml']['path'] == './tests/testfiles/{fileName}.yaml'
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


def test_fetchyaml_pass_with_substitution_string():
    """Relative path to yaml should succeed with path substitution.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileName': 'dict',
        'fetchYaml': './tests/testfiles/{fileName}.yaml'})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['ok1'] == 'ov1'
    assert context['fetchYaml'] == './tests/testfiles/{fileName}.yaml'
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


def test_fetchyaml_list_fails():
    """Yaml describing a list rather than a dict should fail."""
    context = Context({
        'ok1': 'ov1',
        'fetchYaml': './tests/testfiles/list.yaml'})

    with pytest.raises(TypeError):
        filefetcher.run_step(context)


def test_fetchyaml_with_destination():
    """Yaml writes to destination key."""
    context = Context({
        'fetchYaml': {
            'path': '/arb/arbfile',
            'key': 'outkey'}})

    with patch('pypyr.steps.fetchyaml.open', mock_open(
            read_data='[1,2,3]')) as mock_file:
        filefetcher.run_step(context)

    mock_file.assert_called_with('/arb/arbfile')
    assert context['outkey'] == [1, 2, 3]
    assert len(context) == 2


def test_fetchyaml_with_destination_int():
    """Yaml writes to destination key that's not a string."""
    context = Context({
        'fetchYaml': {
            'path': '/arb/arbfile',
            'key': 99}})

    with patch('pypyr.steps.fetchyaml.open', mock_open(read_data='[1,2,3]')):
        filefetcher.run_step(context)

    assert context[99] == [1, 2, 3]
    assert len(context) == 2


def test_fetchyaml_with_destination_formatting():
    """Yaml writes to destination key found by formatting expression."""
    context = Context({
        'keyhere': {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'},
        'fetchYaml': {
            'path': '/arb/{keyhere[arbk]}',
            'key': '{keyhere[sub][0]}'}})

    with patch('pypyr.steps.fetchyaml.open', mock_open(
            read_data='1: 2\n2: 3')) as mock_file:
        filefetcher.run_step(context)

    mock_file.assert_called_with('/arb/arbfile')

    assert len(context) == 3
    assert context['outkey'] == {1: 2, 2: 3}
    assert context['keyhere'] == {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'}
    assert context['fetchYaml'] == {
        'path': '/arb/{keyhere[arbk]}',
        'key': '{keyhere[sub][0]}'}


# ---------------------------- deprecated -------------------------------------
def test_fetchyaml_pass_deprecated():
    """Relative path to yaml should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fetchYamlPath': './tests/testfiles/dict.yaml'})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['ok1'] == 'ov1'
    assert context['fetchYamlPath'] == './tests/testfiles/dict.yaml'
    assert context['fetchYaml'] == {'path': './tests/testfiles/dict.yaml'}
    assert context['key2'] == 'value2', "key2 should be value2"
    assert len(context['key4']['k42']) == 3, "3 items in k42"
    assert 'k42list2' in context['key4']['k42'], "k42 containts k42list2"
    assert context['key4']['k43'], "k43 is True"
    assert context['key4']['k44'] == 77, "k44 is 77"
    assert len(context['key5']) == 2, "2 items in key5"


def test_fetchyaml_with_destination_formatting_deprecated():
    """Yaml writes to destination key found by formatting expression."""
    context = Context({
        'keyhere': {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'},
        'fetchYamlPath': '/arb/{keyhere[arbk]}',
        'fetchYamlKey': '{keyhere[sub][0]}'})

    with patch('pypyr.steps.fetchyaml.open', mock_open(
            read_data='1: 2\n2: 3')) as mock_file:
        filefetcher.run_step(context)

    mock_file.assert_called_with('/arb/arbfile')

    assert len(context) == 5
    assert context['outkey'] == {1: 2, 2: 3}
    assert context['keyhere'] == {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'}
    assert context['fetchYamlPath'] == '/arb/{keyhere[arbk]}'
    assert context['fetchYamlKey'] == '{keyhere[sub][0]}'
    assert context['fetchYaml'] == {'path': '/arb/{keyhere[arbk]}',
                                    'key': '{keyhere[sub][0]}'}
