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


def test_fetchyaml_pass(fs):
    """Relative path to yaml should succeed."""
    payload = """key1: value1
key2: value2
key3: value3
key4:
  k41: k41value
  k42:
    - k42list1
    - k42list2
    - k42list3
  k43: True
  k44: 77
key5:
  - k5list1
  - k5list2
"""

    in_path = './tests/testfiles/dict.yaml'
    fs.create_file(in_path, contents=payload)

    context = Context({
        'ok1': 'ov1',
        'fetchYaml': {
            'path': in_path}})

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


def test_fetchyaml_pass_with_substitution(fs):
    """Relative path to yaml should succeed with path substitution."""
    payload = """key1: value1
key2: value2
key3: value3
key4:
  k41: k41value
  k42:
    - k42list1
    - k42list2
    - k42list3
  k43: True
  k44: 77
key5:
  - k5list1
  - k5list2
"""

    in_path = './tests/testfiles/dict.yaml'
    fs.create_file(in_path, contents=payload)

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


def test_fetchyaml_pass_with_substitution_string(fs):
    """Relative path to yaml should succeed with path substitution."""
    payload = """key1: value1
key2: value2
key3: value3
key4:
  k41: k41value
  k42:
    - k42list1
    - k42list2
    - k42list3
  k43: True
  k44: 77
key5:
  - k5list1
  - k5list2
"""

    in_path = './tests/testfiles/dict.yaml'
    fs.create_file(in_path, contents=payload)
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


def test_fetchyaml_list_fails(fs):
    """Yaml describing a list rather than a dict should fail."""
    payload = """- listitem1
- listitem2
  - listitem2.1
  - listitem2.2
- listitem3
"""

    in_path = './tests/testfiles/list.yaml'
    fs.create_file(in_path, contents=payload)

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

    mock_file.assert_called_with('/arb/arbfile', encoding=None)
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


@patch('pypyr.config.config.default_encoding', new='utf-16')
def test_fetchyaml_with_destination_encoding_config():
    """Get encoding from config."""
    context = Context({
        'keyhere': {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'},
        'fetchYaml': {
            'path': '/arb/{keyhere[arbk]}',
            'key': '{keyhere[sub][0]}'}})

    with patch('pypyr.steps.fetchyaml.open', mock_open(
            read_data='1: 2\n2: 3')) as mock_file:
        filefetcher.run_step(context)

    mock_file.assert_called_with('/arb/arbfile', encoding='utf-16')

    assert len(context) == 3
    assert context['outkey'] == {1: 2, 2: 3}
    assert context['keyhere'] == {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'}
    assert context['fetchYaml'] == {
        'path': '/arb/{keyhere[arbk]}',
        'key': '{keyhere[sub][0]}'}


@patch('pypyr.config.config.default_encoding', new='ascii')
def test_fetchyaml_with_destination_encoding_from_input():
    """Get encoding from input."""
    context = Context({
        'enc': 'utf-16',
        'keyhere': {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'},
        'fetchYaml': {
            'path': '/arb/{keyhere[arbk]}',
            'key': '{keyhere[sub][0]}',
            'encoding': '{enc}'}})

    with patch('pypyr.steps.fetchyaml.open', mock_open(
            read_data='1: 2\n2: 3')) as mock_file:
        filefetcher.run_step(context)

    mock_file.assert_called_with('/arb/arbfile', encoding='utf-16')

    assert len(context) == 4
    assert context['outkey'] == {1: 2, 2: 3}
    assert context['keyhere'] == {'sub': ['outkey', 2, 3], 'arbk': 'arbfile'}
    assert context['fetchYaml'] == {
        'path': '/arb/{keyhere[arbk]}',
        'key': '{keyhere[sub][0]}',
        'encoding': '{enc}'}
