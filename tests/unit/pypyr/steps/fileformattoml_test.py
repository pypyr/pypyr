"""fileformattoml.py unit tests."""
import pytest

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformattoml as fileformat

# region validation


def test_fileformattoml_no_in_obj_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "context['fileFormatToml'] doesn't exist. "
        "It must exist for pypyr.steps.fileformattoml.")


def test_fileformattoml_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'fileFormatToml': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "context['fileFormatToml']['in'] doesn't exist. It must exist for "
        "pypyr.steps.fileformattoml.")


def test_fileformattoml_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatToml': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatToml']['in'] must have "
                                   "a value for pypyr.steps.fileformattoml.")


# endregion validation

# region functional tests
def test_fileformattoml_pass_no_substitutions(fs):
    """Relative path to file should succeed."""
    in_path = './tests/testfiles/test.toml'
    fs.create_file(in_path, contents="""key1 = "value1"
key2 = "value2"
key3 = "value3"
""", encoding='utf-8')

    context = Context({
        'ok1': 'ov1',
        'fileFormatToml': {'in': in_path,
                           'out': './tests/testfiles/out/out.toml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatToml'] == {
        'in': in_path,
        'out': './tests/testfiles/out/out.toml'}

    with open('./tests/testfiles/out/out.toml') as outfile:
        outcontents = outfile.read()

    assert outcontents == """key1 = "value1"
key2 = "value2"
key3 = "value3"
"""


def test_fileformattoml_pass_to_out_dir(fs):
    """Relative path to file succeed with out dir rather than full path."""
    in_path = './tests/testfiles/test.toml'
    fs.create_file(in_path, contents="""key1 = "value1"
key2 = "value2"
key3 = "value3"
""", encoding='utf-8')

    context = Context({
        'ok1': 'ov1',
        'fileFormatToml': {'in': in_path,
                           'out': './tests/testfiles/out/'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatToml'] == {
        'in': in_path,
        'out': './tests/testfiles/out/'}

    with open('./tests/testfiles/out/test.toml', encoding='utf-8') as outfile:
        outcontents = outfile.read()

    assert outcontents == """key1 = "value1"
key2 = "value2"
key3 = "value3"
"""


def test_fileformattoml_edit_no_substitutions(fs):
    """Relative path to file should succeed, no out means in place edit."""
    in_path = './tests/testfiles/out/edittest.toml'
    fs.create_file(in_path, contents="""key1 = "value1"
key2 = "value2"
key3 = "value3"
""", encoding='utf-8')

    context = Context({
        'ok1': 'ov1',
        'fileFormatToml': {'in': './tests/testfiles/out/edittest.toml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatToml'] == {
        'in': './tests/testfiles/out/edittest.toml'}

    with open('./tests/testfiles/out/edittest.toml',
              encoding='utf-8') as outfile:
        outcontents = outfile.read()

    assert outcontents == """key1 = "value1"
key2 = "value2"
key3 = "value3"
"""


def test_fileformattoml_pass_with_substitutions(fs):
    """Relative path to file should succeed."""
    in_path = './tests/testfiles/testsubst.toml'
    fs.create_file(in_path, contents="""key1 = "{k1}value !£$% *"
["key2_{k2}"]
abc = "{k3} def {k4}"
def = [
  "l1",
  "l2 {k5}",
  "l3",
]
k21 = "value"
""", encoding='utf-8')
    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatToml': {'in': in_path,
                           'out': './tests/testfiles/out/outsubst.toml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatToml'] == {
        'in': './tests/testfiles/testsubst.toml',
        'out': './tests/testfiles/out/outsubst.toml'}

    with open('./tests/testfiles/out/outsubst.toml',
              encoding='utf-8') as outfile:
        outcontents = outfile.read()

    expected = """key1 = "v1value !£$% *"

[key2_v2]
abc = "v3 def v4"
def = [
    "l1",
    "l2 v5",
    "l3",
]
k21 = "value"
"""

    assert outcontents == expected


def test_fileformattoml_pass_with_path_substitutions(fs):
    """Relative path to file should succeed with path substitutions."""
    in_path = './tests/testfiles/testsubst.toml'
    fs.create_file(in_path, contents="""key1 = "{k1}value !£$% *"
["key2_{k2}"]
abc = "{k3} def {k4}"
def = [
  "l1",
  "l2 {k5}",
  "l3",
]
k21 = "value"
""", encoding='utf-8')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'pathIn': 'testsubst',
        'pathOut': 'outsubst',
        'fileFormatToml': {'in': './tests/testfiles/{pathIn}.toml',
                           'out': './tests/testfiles/out/{pathOut}.toml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatToml'] == {
        'in': './tests/testfiles/{pathIn}.toml',
        'out': './tests/testfiles/out/{pathOut}.toml'}

    with open('./tests/testfiles/out/outsubst.toml',
              encoding='utf-8') as outfile:
        outcontents = outfile.read()

    expected = """key1 = "v1value !£$% *"

[key2_v2]
abc = "v3 def v4"
def = [
    "l1",
    "l2 v5",
    "l3",
]
k21 = "value"
"""

    assert outcontents == expected


def test_fileformattoml_with_encoding(fs):
    """Toml parses binary for utf-8 only, no encoding allowed."""
    in_path = './tests/testfiles/test.toml'
    fs.create_file(in_path, contents='key1 = "value"')

    context = Context({
        'ok1': 'ov1',
        'fileFormatToml': {'in': in_path,
                           'out': 'test/out/output.toml',
                           'encoding': 'utf-16'}})

    with pytest.raises(ValueError) as err:
        fileformat.run_step(context)

    assert str(err.value) == "binary mode doesn't take an encoding argument"

# endregion functional tests
