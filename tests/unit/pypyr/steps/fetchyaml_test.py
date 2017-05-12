"""fetchyaml.py unit tests."""
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

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fetchYamlPath'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.fetchyaml.\",)")


def test_fetchyaml_empty_path_raises():
    """Empty path raises."""
    context = Context({
        'fetchYamlPath': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filefetcher.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fetchYamlPath'] must have a "
        "value for pypyr.steps.fetchyaml.\",)")


def test_fetchyaml_pass():
    """Relative path to yaml should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fetchYamlPath': './tests/testfiles/dict.yaml'})

    filefetcher.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 5 items"
    assert context['ok1'] == 'ov1'
    assert context['fetchYamlPath'] == './tests/testfiles/dict.yaml'
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
        'fetchYamlPath': './tests/testfiles/list.yaml'})

    with pytest.raises(TypeError):
        filefetcher.run_step(context)
