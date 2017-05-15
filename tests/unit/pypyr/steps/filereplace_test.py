"""fileformat.py unit tests."""
import os
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.filereplace as filereplace
import pytest


# ------------------------ arg validation -------------------------------------
def test_filereplace_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fileReplaceIn'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.filereplace.\",)")


def test_filereplace_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileReplaceIn': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fileReplaceIn'] must have a "
        "value for pypyr.steps.filereplace.\",)")


def test_filereplace_no_outpath_raises():
    """None out path raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fileReplaceOut'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.filereplace.\",)")


def test_filereplace_empty_outpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'fileReplaceOut': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fileReplaceOut'] must have a "
        "value for pypyr.steps.filereplace.\",)")


def test_filereplace_no_replacepairs_raises():
    """None replacepairs raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'fileReplaceOut': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fileReplacePairs'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.filereplace.\",)")


def test_filereplace_empty_replacepairs_raises():
    """Empty in path raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'fileReplaceOut': 'blah',
        'fileReplacePairs': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fileReplacePairs'] must have "
        "a value for pypyr.steps.filereplace.\",)")

# ------------------------ arg validation -------------------------------------

# ------------------------ run_step -------------------------------------------


def test_filereplace_pass_no_matches():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileReplaceIn': './tests/testfiles/test.txt',
        'fileReplaceOut': './tests/testfiles/out/outreplace.txt',
        'fileReplacePairs': {
            'XXXXX': 'doesnt exist',
            'YYYYY': 'doesnt exist either'
        }})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 4, "context should have 4 items"
    assert context['ok1'] == 'ov1'
    assert context['fileReplaceIn'] == './tests/testfiles/test.txt'
    assert context['fileReplaceOut'] == './tests/testfiles/out/outreplace.txt'

    with open('./tests/testfiles/out/outreplace.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this is line 1\n"
    assert outcontents[1] == "this is line 2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this is line 4\n"
    assert outcontents[4] == "this !£$% * is line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outreplace.txt')


def test_filereplace_pass_with_replacements():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'X1',
        'fileReplaceIn': './tests/testfiles/testreplace.txt',
        'fileReplaceOut': './tests/testfiles/out/outreplace.txt',
        'fileReplacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5',
        }})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 4, "context should have 4 items"
    assert context['k1'] == 'X1'
    assert context['fileReplaceIn'] == './tests/testfiles/testreplace.txt'
    assert context['fileReplaceOut'] == './tests/testfiles/out/outreplace.txt'

    with open('./tests/testfiles/out/outreplace.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this {k1} v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this rm3 v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outreplace.txt')

# ------------------------ run_step -------------------------------------------

# ------------------------ iter_replace_strings--------------------------------


def test_iter_replace_string_empties():
    """Nothing in, nothing out"""
    in_string = ''
    replace_pairs = {}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert not result


def test_iter_replace_string_one_none():
    """One in, none out"""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'ten': '10'}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert result == in_string


def test_iter_replace_string_one_one():
    """One in, one out"""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'six': '6'}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert result[0] == 'one two three four five 6 seven eight'


def test_iter_replace_string_two_one():
    """Two in, one out"""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'six': '6', 'XXX': '3'}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert result[0] == 'one two three four five 6 seven eight'


def test_iter_replace_string_two_two():
    """Two in, two out"""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'six': '6', 'three': '3'}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert result[0] == 'one two 3 four five 6 seven eight'


def test_iter_replace_string_instring_actually_iterates():
    """Iterates over an in iterable"""
    in_string = ['one two three', 'four five six', 'seven eight nine']
    replace_pairs = {'six': '6', 'three': '3'}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert result[0] == 'one two 3'
    assert result[1] == 'four five 6'
    assert result[2] == 'seven eight nine'


def test_iter_replace_string_later_replace_earlier():
    """A later replacement replaces one from earlier"""
    in_string = ['one two three', 'four five six', 'seven eight nine']
    replace_pairs = {'six': '6', 'three': '3', '6': 'XXX'}
    result = list(filereplace.iter_replace_strings(in_string, replace_pairs))
    assert result[0] == 'one two 3'
    assert result[1] == 'four five XXX'
    assert result[2] == 'seven eight nine'

# ------------------------ iter_replace_strings--------------------------------

# ------------------------ setup/teardown -------------------------------------


def teardown_module(module):
    """Teardown"""
    os.rmdir('./tests/testfiles/out/')
