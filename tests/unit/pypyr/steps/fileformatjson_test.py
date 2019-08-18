"""fileformatjson.py unit tests."""
import os
import json
import shutil
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformatjson as fileformat
import pytest


def test_fileformatjson_no_in_obj_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "fileFormatJson not found in the pypyr context.")


def test_fileformatjson_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'fileFormatJson': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "context['fileFormatJson']['in'] doesn't exist. It must exist for "
        "pypyr.steps.fileformatjson.")


def test_fileformatjson_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatJson': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatJson']['in'] must have "
                                   "a value for pypyr.steps.fileformatjson.")


def test_fileformatjson_pass_no_substitutions():
    """Relative path to file should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileFormatJson': {'in': './tests/testfiles/test.json',
                           'out': './tests/testfiles/out/out.json'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatJson'] == {
        'in': './tests/testfiles/test.json',
        'out': './tests/testfiles/out/out.json'}

    with open('./tests/testfiles/out/out.json') as outfile:
        outcontents = json.load(outfile)

    assert len(outcontents) == 3
    assert outcontents['key1'] == "value1"
    assert outcontents['key2'] == "value2"
    assert outcontents['key3'] == "value3"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/out.json')


def test_fileformatjson_edit_no_substitutions():
    """Relative path to file should succeed, no out means in place edit.

    Strictly speaking not a unit test.
    """
    shutil.copyfile('./tests/testfiles/test.json',
                    './tests/testfiles/out/edittest.json')

    context = Context({
        'ok1': 'ov1',
        'fileFormatJson': {'in': './tests/testfiles/out/edittest.json'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatJson'] == {
        'in': './tests/testfiles/out/edittest.json'}

    with open('./tests/testfiles/out/edittest.json') as outfile:
        outcontents = json.load(outfile)

    assert len(outcontents) == 3
    assert outcontents['key1'] == "value1"
    assert outcontents['key2'] == "value2"
    assert outcontents['key3'] == "value3"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/edittest.json')


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
        'fileFormatJson': {'in': './tests/testfiles/testsubst.json',
                           'out': './tests/testfiles/out/outsubst.json'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatJson'] == {
        'in': './tests/testfiles/testsubst.json',
        'out': './tests/testfiles/out/outsubst.json'}

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
        'fileFormatJson': {'in': './tests/testfiles/{pathIn}.json',
                           'out': './tests/testfiles/out/{pathOut}.json'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatJson'] == {
        'in': './tests/testfiles/{pathIn}.json',
        'out': './tests/testfiles/out/{pathOut}.json'}

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

# --------------------------- teardown ---------------------------------------


def teardown_module(module):
    """Teardown."""
    os.rmdir('./tests/testfiles/out/')
