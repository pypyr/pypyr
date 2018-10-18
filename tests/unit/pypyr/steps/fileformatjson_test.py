"""fileformatjson.py unit tests."""
import os
import json
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformatjson as fileformat
import pytest


def test_fileformatjson_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatJsonIn'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileformatjson.")


def test_fileformatjson_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatJsonIn': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatJsonIn'] must have "
                                   "a value for pypyr.steps.fileformatjson.")


def test_fileformatjson_no_outpath_raises():
    """None out path raises."""
    context = Context({
        'fileFormatJsonIn': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatJsonOut'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileformatjson.")


def test_fileformatjson_empty_outpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatJsonIn': 'blah',
        'fileFormatJsonOut': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatJsonOut'] must have "
                                   "a value for pypyr.steps.fileformatjson.")


def test_fileformatjson_pass_no_substitutions():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileFormatJsonIn': './tests/testfiles/test.json',
        'fileFormatJsonOut': './tests/testfiles/out/out.json'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatJsonIn'] == './tests/testfiles/test.json'
    assert context['fileFormatJsonOut'] == './tests/testfiles/out/out.json'

    with open('./tests/testfiles/out/out.json') as outfile:
        outcontents = json.load(outfile)

    assert len(outcontents) == 3
    assert outcontents['key1'] == "value1"
    assert outcontents['key2'] == "value2"
    assert outcontents['key3'] == "value3"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/out.json')


def test_fileformatjson_pass_with_substitutions():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatJsonIn': './tests/testfiles/testsubst.json',
        'fileFormatJsonOut': './tests/testfiles/out/outsubst.json'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatJsonIn'] == './tests/testfiles/testsubst.json'
    assert context['fileFormatJsonOut'] == ('./tests/testfiles/out/'
                                            'outsubst.json')

    with open('./tests/testfiles/out/outsubst.json') as outfile:
        outcontents = json.load(outfile)

    expected = {
        "key1": "v1value !£$% *",
        "key2_v2": {
            "k21": "value",
            "abc": "v3 def v4",
            "def": [
                "l1",
                "l2 v5",
                "l3"
            ]
        }
    }

    assert outcontents == expected

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.json')


def test_fileformatjson_pass_with_path_substitutions():
    """Relative path to file should succeed with path subsitutions.

     Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'pathIn': 'testsubst',
        'pathOut': 'outsubst',
        'fileFormatJsonIn': './tests/testfiles/{pathIn}.json',
        'fileFormatJsonOut': './tests/testfiles/out/{pathOut}.json'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatJsonIn'] == './tests/testfiles/{pathIn}.json'
    assert context['fileFormatJsonOut'] == ('./tests/testfiles/out/'
                                            '{pathOut}.json')

    with open('./tests/testfiles/out/outsubst.json') as outfile:
        outcontents = json.load(outfile)

    expected = {
        "key1": "v1value !£$% *",
        "key2_v2": {
            "k21": "value",
            "abc": "v3 def v4",
            "def": [
                "l1",
                "l2 v5",
                "l3"
            ]
        }
    }

    assert outcontents == expected

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.json')


def teardown_module(module):
    """Teardown"""
    os.rmdir('./tests/testfiles/out/')
