"""fileformat.py unit tests."""
import os
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformat as fileformat
import pytest


def test_fileformat_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatIn'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileformat.")


def test_fileformat_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatIn': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatIn'] must have a "
                                   "value for pypyr.steps.fileformat.")


def test_fileformat_no_outpath_raises():
    """None out path raises."""
    context = Context({
        'fileFormatIn': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatOut'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileformat.")


def test_fileformat_empty_outpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatIn': 'blah',
        'fileFormatOut': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatOut'] must have a "
                                   "value for pypyr.steps.fileformat.")


def test_fileformat_pass_no_substitutions():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileFormatIn': './tests/testfiles/test.txt',
        'fileFormatOut': './tests/testfiles/out/out.txt'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatIn'] == './tests/testfiles/test.txt'
    assert context['fileFormatOut'] == './tests/testfiles/out/out.txt'

    with open('./tests/testfiles/out/out.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this is line 1\n"
    assert outcontents[1] == "this is line 2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this is line 4\n"
    assert outcontents[4] == "this !£$% * is line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/out.txt')


def test_fileformat_pass_with_substitutions():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatIn': './tests/testfiles/testsubst.txt',
        'fileFormatOut': './tests/testfiles/out/outsubst.txt'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatIn'] == './tests/testfiles/testsubst.txt'
    assert context['fileFormatOut'] == './tests/testfiles/out/outsubst.txt'

    with open('./tests/testfiles/out/outsubst.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.txt')


def test_fileformat_pass_with_path_substitutions():
    """Relative path to file should succeed with path subsitutions.

     Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'inFileName': 'testsubst',
        'outFileName': 'outsubst',
        'fileFormatIn': './tests/testfiles/{inFileName}.txt',
        'fileFormatOut': './tests/testfiles/out/{outFileName}.txt'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatIn'] == './tests/testfiles/{inFileName}.txt'
    assert context['fileFormatOut'] == (
        './tests/testfiles/out/{outFileName}.txt')

    with open('./tests/testfiles/out/outsubst.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.txt')


def teardown_module(module):
    """Teardown"""
    os.rmdir('./tests/testfiles/out/')
