"""fileformat.py unit tests."""
import logging
import os
import pytest
import shutil
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformat as fileformat
from tests.common.utils import patch_logger


def test_fileformat_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "fileFormat not found in the pypyr context.")


def test_fileformat_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormat': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormat']['in'] must have a "
                                   "value for pypyr.steps.fileformat.")


def test_fileformat_pass_no_substitutions():
    """Relative path to file should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileFormat': {'in': './tests/testfiles/test.txt',
                       'out': './tests/testfiles/out/out.txt'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormat'] == {'in': './tests/testfiles/test.txt',
                                     'out': './tests/testfiles/out/out.txt'}

    with open('./tests/testfiles/out/out.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this is line 1\n"
    assert outcontents[1] == "this is line 2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this is line 4\n"
    assert outcontents[4] == "this !£$% * is line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/out.txt')


def test_fileformat_edit_no_substitutions():
    """Relative path to file should succeed and edit in place when no out.

    Strictly speaking not a unit test.
    """
    shutil.copyfile('./tests/testfiles/test.txt',
                    './tests/testfiles/out/edittest.txt')
    context = Context({
        'ok1': 'ov1',
        'fileFormat': {'in': './tests/testfiles/out/edittest.txt'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormat'] == {
        'in': './tests/testfiles/out/edittest.txt'}

    with open('./tests/testfiles/out/edittest.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this is line 1\n"
    assert outcontents[1] == "this is line 2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this is line 4\n"
    assert outcontents[4] == "this !£$% * is line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/edittest.txt')


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
        'fileFormat': {'in': './tests/testfiles/testsubst.txt',
                       'out': './tests/testfiles/out/outsubst.txt'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormat'] == {
        'in': './tests/testfiles/testsubst.txt',
        'out': './tests/testfiles/out/outsubst.txt'}

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
    """Relative path to file should succeed with path substitutions.

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
        'fileFormat': {'in': './tests/testfiles/{inFileName}.txt',
                       'out': './tests/testfiles/out/{outFileName}.txt'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['k1'] == 'v1'
    assert context['fileFormat'] == {
        'in': './tests/testfiles/{inFileName}.txt',
        'out': './tests/testfiles/out/{outFileName}.txt'}

    with open('./tests/testfiles/out/outsubst.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.txt')


# -------------------------- deprecated ---------------------------------------

def test_fileformat_pass_with_path_substitutions_deprecated():
    """Relative path to file should succeed with path substitutions.

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

    with patch_logger(
            'pypyr.steps.fileformat', logging.WARNING
    ) as mock_logger_warn:
        fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 10, "context should have 10 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatIn'] == './tests/testfiles/{inFileName}.txt'
    assert context['fileFormatOut'] == (
        './tests/testfiles/out/{outFileName}.txt')
    assert context['fileFormat'] == {
        'in': './tests/testfiles/{inFileName}.txt',
        'out': './tests/testfiles/out/{outFileName}.txt'
    }

    with open('./tests/testfiles/out/outsubst.txt') as outfile:
        outcontents = list(outfile)

    mock_logger_warn.assert_called_once_with(
        "fileFormatIn and fileFormatOut are deprecated. They will stop "
        "working upon the next major release. Use the new context key "
        "fileFormat instead. It's a lot better, promise! For the moment pypyr "
        "is creating the new fileFormat key for you under the hood.")
    assert outcontents[0] == "this v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.txt')


def test_fileformat_empty_inpath_raises_dewprecated():
    """Empty in path raises."""
    context = Context({
        'fileFormatIn': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatIn'] must have a "
                                   "value for pypyr.steps.fileformat.")


def test_fileformat_no_outpath_raises_deprecated():
    """None out path raises."""
    context = Context({
        'fileFormatIn': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatOut'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.fileformat.")


def test_fileformat_empty_outpath_raises_deprecated():
    """Empty in path raises."""
    context = Context({
        'fileFormatIn': 'blah',
        'fileFormatOut': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatOut'] must have a "
                                   "value for pypyr.steps.fileformat.")


# -------------------------------- deprecated ---------------------------------
def teardown_module(module):
    """Teardown."""
    os.rmdir('./tests/testfiles/out/')
