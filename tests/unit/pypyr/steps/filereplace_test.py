"""fileformat.py unit tests."""
import pytest

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.filereplace as filereplace


# region arg validation
def test_filereplace_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        filereplace.run_step(context)

    assert str(err_info.value) == (
        "context['fileReplace'] doesn't exist. "
        "It must exist for pypyr.steps.filereplace.")


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

# endregion arg validation

# region run_step


def test_filereplace_pass_no_matches(fs):
    """Relative path to file should succeed."""
    payload = ('this is line 1\n'
               'this is line 2\n'
               'this is line 3\n'
               'this is line 4\n'
               'this !£$% * is line 5\n')

    in_path = './tests/testfiles/test.txt'
    fs.create_file(in_path, contents=payload)

    context = Context({
        'ok1': 'ov1',
        'fileReplace': {'in': in_path,
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
        outcontents = outfile.read()

    assert outcontents == payload


def test_filereplace_pass_with_replacements(fs):
    """Relative path to file should succeed.

    Strictly speaking not a unit test.
    """
    payload = ('this {k1} X1 is line 1\n'
               'this is line 2 REPLACEME2\n'
               'this is line 3\n'
               'this rm3 RM3 is  RM4 line 4\n'
               'this !£$% * is rm5 line 5\n')

    in_path = './tests/testfiles/testreplace.txt'
    fs.create_file(in_path, contents=payload)

    context = Context({
        'k1': 'X1',
        'fileReplace': {'in': in_path,
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
        'in': in_path,
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


def test_filereplace_pass_with_substitutions(fs):
    """Relative path to file should succeed with input substitutions."""
    payload = ('this {k1} X1 is line 1\n'
               'this is line 2 REPLACEME2\n'
               'this is line 3\n'
               'this rm3 RM3 is  RM4 line 4\n'
               'this !£$% * is rm5 line 5\n')

    in_path = './tests/testfiles/testreplace.txt'
    fs.create_file(in_path, contents=payload, encoding='utf-16')

    context = Context({
        'k1': 'X1',
        'inFile': 'testreplace',
        'outFile': 'outreplace',
        'enc': 'utf-16',
        'fileReplace': {'in': './tests/testfiles/{inFile}.txt',
                        'out': './tests/testfiles/out/{outFile}.txt',
                        'encoding': '{enc}',
                        'replacePairs': {
                            '{k1}': 'v1',
                            'REPLACEME2': 'v2',
                            'RM3': 'v3',
                            'RM4': 'v4',
                            'rm5': 'v5'}}})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['k1'] == 'X1'
    assert context['fileReplace'] == {
        'in': './tests/testfiles/{inFile}.txt',
        'out': './tests/testfiles/out/{outFile}.txt',
        'encoding': '{enc}',
        'replacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5'}}

    with open('./tests/testfiles/out/outreplace.txt',
              encoding='utf-16') as file:
        outcontent = file.read()

    expected = ("this {k1} v1 is line 1\n"
                "this is line 2 v2\n"
                "this is line 3\n"
                "this rm3 v3 is  v4 line 4\n"
                "this !£$% * is v5 line 5\n")

    assert outcontent == expected


def test_filereplace_pass_out_is_dir(fs):
    """Relative path to file should write same filename if out is dir."""
    payload = ('this {k1} X1 is line 1\n'
               'this is line 2 REPLACEME2\n'
               'this is line 3\n'
               'this rm3 RM3 is  RM4 line 4\n'
               'this !£$% * is rm5 line 5\n')

    in_path = '/testreplace.txt'
    fs.create_file(in_path, contents=payload)

    context = Context({
        'k1': 'X1',
        'inFile': 'testreplace',
        'outDir': '/out/',
        'enc': 'utf-16',
        'fileReplace': {'in': '/{inFile}.txt',
                        'out': '{outDir}',
                        'encodingOut': '{enc}',
                        'replacePairs': {
                            '{k1}': 'v1',
                            'REPLACEME2': 'v2',
                            'RM3': 'v3',
                            'RM4': 'v4',
                            'rm5': 'v5'}}})

    filereplace.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 5, "context should have 5 items"
    assert context['k1'] == 'X1'
    assert context['fileReplace'] == {
        'in': '/{inFile}.txt',
        'out': '{outDir}',
        'encodingOut': '{enc}',
        'replacePairs': {
            '{k1}': 'v1',
            'REPLACEME2': 'v2',
            'RM3': 'v3',
            'RM4': 'v4',
            'rm5': 'v5'}}

    with open('/out/testreplace.txt', encoding='utf-16') as file:
        outcontent = file.read()

    expected = ("this {k1} v1 is line 1\n"
                "this is line 2 v2\n"
                "this is line 3\n"
                "this rm3 v3 is  v4 line 4\n"
                "this !£$% * is v5 line 5\n")

    assert outcontent == expected


def test_filereplace_pass_out_encoding_in_to_out(fs):
    """Change encoding from in to out."""
    payload = ('this {k1} X1 is line 1\n'
               'this is line 2 REPLACEME2\n'
               'this is line 3\n'
               'this rm3 RM3 is  RM4 line 4\n'
               'this !£$% * is rm5 line 5\n')

    in_path = '/testreplace.txt'
    fs.create_file(in_path, contents=payload, encoding='utf-32')

    context = Context({
        'k1': 'X1',
        'inFile': 'testreplace',
        'outDir': '/out/',
        'encIn': 'utf-32',
        'encOut': 'utf-16',
        'fileReplace': {'in': '/{inFile}.txt',
                        'out': '{outDir}',
                        'encodingIn': '{encIn}',
                        'encodingOut': '{encOut}',
                        'replacePairs': {
                            '{k1}': 'v1',
                            'REPLACEME2': 'v2',
                            'RM3': 'v3',
                            'RM4': 'v4',
                            'rm5': 'v5'}}})

    filereplace.run_step(context)

    with open('/out/testreplace.txt', encoding='utf-16') as file:
        outcontent = file.read()

    expected = ("this {k1} v1 is line 1\n"
                "this is line 2 v2\n"
                "this is line 3\n"
                "this rm3 v3 is  v4 line 4\n"
                "this !£$% * is v5 line 5\n")

    assert outcontent == expected
# endregion run_step
