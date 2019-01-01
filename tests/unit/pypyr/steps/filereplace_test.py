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

    assert str(err_info.value) == (
        "fileReplace not found in the pypyr context.")


def test_filereplace_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileReplace': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplace']['in'] must have a "
                                   "value for pypyr.steps.filereplace.")


def test_filereplace_no_replacepairs_raises():
    """None replacepairs raises."""
    context = Context({
        'fileReplace': {'in': 'blah',
                        'out': 'blah',
                        'k1': 'v1'}})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplace']['replacePairs'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filereplace.")


def test_filereplace_empty_replacepairs_raises():
    """Empty in path raises."""
    context = Context({
        'fileReplace': {'in': 'blah',
                        'out': 'blah',
                        'replacePairs': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == (
        "context['fileReplace']['replacePairs'] must have "
        "a value for pypyr.steps.filereplace.")

# ------------------------ arg validation -------------------------------------

# ------------------------ run_step -------------------------------------------


def test_filereplace_pass_no_matches():
    """Relative path to file should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileReplace': {'in': './tests/testfiles/test.txt',
                        'out': './tests/testfiles/out/outreplace.txt',
                        'replacePairs': {
                            'XXXXX': 'doesnt exist',
                            'YYYYY': 'doesnt exist either'
                        }}})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileReplace'] == {
        'in': './tests/testfiles/test.txt',
        'out': './tests/testfiles/out/outreplace.txt',
        'replacePairs': {
            'XXXXX': 'doesnt exist',
            'YYYYY': 'doesnt exist either'
        }}

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
        'fileReplace': {'in': './tests/testfiles/testreplace.txt',
                        'out': './tests/testfiles/out/outreplace.txt',
                        'replacePairs': {
                            '{k1}': 'v1',
                            'REPLACEME2': 'v2',
                            'RM3': 'v3',
                            'RM4': 'v4',
                            'rm5': 'v5',
                        }}})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['k1'] == 'X1'
    assert context['fileReplace'] == {
        'in': './tests/testfiles/testreplace.txt',
        'out': './tests/testfiles/out/outreplace.txt',
        'replacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5',
        }}
    with open('./tests/testfiles/out/outreplace.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this {k1} v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this rm3 v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outreplace.txt')


def test_filereplace_pass_with_path_replacements():
    """Relative path to file should succeed with path replacements.

    Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'X1',
        'inFile': 'testreplace',
        'outFile': 'outreplace',
        'fileReplace': {'in': './tests/testfiles/{inFile}.txt',
                        'out': './tests/testfiles/out/{outFile}.txt',
                        'replacePairs': {
                            '{k1}': 'v1',
                            'REPLACEME2': 'v2',
                            'RM3': 'v3',
                            'RM4': 'v4',
                            'rm5': 'v5'}}})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 4, "context should have 4 items"
    assert context['k1'] == 'X1'
    assert context['fileReplace'] == {
        'in': './tests/testfiles/{inFile}.txt',
        'out': './tests/testfiles/out/{outFile}.txt',
        'replacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5'}}

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

# ------------------------ deprecated -----------------------------------------


def test_filereplace_empty_inpath_raises_deprecated():
    """Empty in path raises."""
    context = Context({
        'fileReplaceIn': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplaceIn'] must have a "
                                   "value for pypyr.steps.filereplace.")


def test_filereplace_no_outpath_raises_deprecated():
    """None out path raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplaceOut'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filereplace.")


def test_filereplace_empty_outpath_raises_deprecated():
    """Empty in path raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'fileReplaceOut': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplaceOut'] must have a "
                                   "value for pypyr.steps.filereplace.")


def test_filereplace_no_replacepairs_raises_deprecated():
    """None replacepairs raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'fileReplaceOut': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplacePairs'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.filereplace.")


def test_filereplace_empty_replacepairs_raises_deprecated():
    """Empty in path raises."""
    context = Context({
        'fileReplaceIn': 'blah',
        'fileReplaceOut': 'blah',
        'fileReplacePairs': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == ("context['fileReplacePairs'] must have "
                                   "a value for pypyr.steps.filereplace.")


def test_filereplace_pass_with_path_replacements_deprecated():
    """Relative path to file should succeed with path replacements.

    Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'X1',
        'inFile': 'testreplace',
        'outFile': 'outreplace',
        'fileReplaceIn': './tests/testfiles/{inFile}.txt',
        'fileReplaceOut': './tests/testfiles/out/{outFile}.txt',
        'fileReplacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5',
        }})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['k1'] == 'X1'
    assert context['fileReplaceIn'] == './tests/testfiles/{inFile}.txt'
    assert context['fileReplaceOut'] == './tests/testfiles/out/{outFile}.txt'
    assert context['fileReplace'] == {
        'in': './tests/testfiles/{inFile}.txt',
        'out': './tests/testfiles/out/{outFile}.txt',
        'replacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5'}}

    with open('./tests/testfiles/out/outreplace.txt') as outfile:
        outcontents = list(outfile)

    assert outcontents[0] == "this {k1} v1 is line 1\n"
    assert outcontents[1] == "this is line 2 v2\n"
    assert outcontents[2] == "this is line 3\n"
    assert outcontents[3] == "this rm3 v3 is  v4 line 4\n"
    assert outcontents[4] == "this !£$% * is v5 line 5\n"

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outreplace.txt')

# ------------------------ setup/teardown -------------------------------------


def teardown_module(module):
    """Teardown."""
    os.rmdir('./tests/testfiles/out/')
