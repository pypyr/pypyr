"""fileformat.py unit tests."""
from unittest.mock import patch

import pytest

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformat as fileformat


def test_fileformat_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "context['fileFormat'] doesn't exist. "
        "It must exist for pypyr.steps.fileformat.")


def test_fileformat_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormat': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormat']['in'] must have a "
                                   "value for pypyr.steps.fileformat.")


def test_fileformat_pass_no_substitutions(fs):
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
        'fileFormat': {'in': in_path,
                       'out': './tests/testfiles/out/out.txt'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormat'] == {'in': in_path,
                                     'out': './tests/testfiles/out/out.txt'}

    with open('./tests/testfiles/out/out.txt') as outfile:
        outcontents = outfile.read()

    assert outcontents == payload


def test_fileformat_edit_no_substitutions(fs):
    """Relative path to file should succeed and edit in place when no out."""
    payload = ('this is line 1\n'
               'this is line 2\n'
               'this is line 3\n'
               'this is line 4\n'
               'this !£$% * is line 5\n')

    in_path = './tests/testfiles/out/edittest.txt'
    fs.create_file(in_path, contents=payload)
    context = Context({
        'ok1': 'ov1',
        'fileFormat': {'in': in_path}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormat'] == {
        'in': in_path}

    with open(in_path) as outfile:
        outcontents = outfile.read()

    assert outcontents == payload


def test_fileformat_pass_with_substitutions(fs):
    """Relative path to file should succeed."""
    payload = """this {k1} is line 1
this is line 2 {k2}
this is line 3
this {k3} is  {k4} line 4
this !£$% * is {k5} line 5
"""

    in_path = './tests/testfiles/testsubst.txt'
    fs.create_file(in_path, contents=payload)

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
        outcontents = outfile.read()

    assert outcontents == """this v1 is line 1
this is line 2 v2
this is line 3
this v3 is  v4 line 4
this !£$% * is v5 line 5
"""


def test_fileformat_pass_with_path_substitutions(fs):
    """Relative path to file should succeed with path substitutions."""
    payload = """this {k1} is line 1
this is line 2 {k2}
this is line 3
this {k3} is  {k4} line 4
this !£$% * is {k5} line 5
"""

    in_path = './tests/testfiles/testsubst.txt'
    fs.create_file(in_path, contents=payload)

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
        outcontents = outfile.read()

    assert outcontents == """this v1 is line 1
this is line 2 v2
this is line 3
this v3 is  v4 line 4
this !£$% * is v5 line 5
"""


@patch('pypyr.config.config.default_encoding', new='utf-16')
def test_fileformat_pass_with_encoding_from_config(fs):
    """Get encoding from config."""
    payload = """this {k1} is line 1
this is line 2 {k2}
this is line 3
this {k3} is  {k4} line 4
this !£$% * is {k5} line 5
"""

    in_path = './tests/testfiles/testsubst.txt'
    fs.create_file(in_path, contents=payload, encoding='utf-16')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'enc': 'utf-16',
        'inFileName': 'testsubst',
        'outFileName': 'outsubst',
        'fileFormat': {'in': './tests/testfiles/{inFileName}.txt',
                       'out': './tests/testfiles/out/{outFileName}.txt'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormat'] == {
        'in': './tests/testfiles/{inFileName}.txt',
        'out': './tests/testfiles/out/{outFileName}.txt'}

    with open('./tests/testfiles/out/outsubst.txt',
              encoding='utf-16') as outfile:
        outcontents = outfile.read()

    assert outcontents == """this v1 is line 1
this is line 2 v2
this is line 3
this v3 is  v4 line 4
this !£$% * is v5 line 5
"""


def test_fileformat_pass_with_encoding(fs):
    """Pass encoding with input."""
    payload = """this {k1} is line 1
this is line 2 {k2}
this is line 3
this {k3} is  {k4} line 4
this !£$% * is {k5} line 5
"""

    in_path = './tests/testfiles/testsubst.txt'
    fs.create_file(in_path, contents=payload, encoding='utf-16')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'enc': 'utf-16',
        'inFileName': 'testsubst',
        'outFileName': 'outsubst',
        'fileFormat': {'in': './tests/testfiles/{inFileName}.txt',
                       'out': './tests/testfiles/out/{outFileName}.txt',
                       'encoding': '{enc}'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormat'] == {
        'in': './tests/testfiles/{inFileName}.txt',
        'out': './tests/testfiles/out/{outFileName}.txt',
        'encoding': '{enc}'}

    with open('./tests/testfiles/out/outsubst.txt',
              encoding='utf-16') as outfile:
        outcontents = outfile.read()

    assert outcontents == """this v1 is line 1
this is line 2 v2
this is line 3
this v3 is  v4 line 4
this !£$% * is v5 line 5
"""


def test_fileformat_pass_with_encoding_in_to_out(fs):
    """Pass encoding with input and output."""
    payload = """this {k1} is line 1
this is line 2 {k2}
this is line 3
this {k3} is  {k4} line 4
this !£$% * is {k5} line 5
"""

    in_path = './tests/testfiles/testsubst.txt'
    fs.create_file(in_path, contents=payload, encoding='utf-16')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'encIn': 'utf-16',
        'encOut': 'utf-32',
        'inFileName': 'testsubst',
        'outFileName': 'outsubst',
        'fileFormat': {'in': './tests/testfiles/{inFileName}.txt',
                       'out': './tests/testfiles/out/{outFileName}.txt',
                       'encodingIn': '{encIn}',
                       'encodingOut': '{encOut}'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 10, "context should have 10 items"
    assert context['k1'] == 'v1'
    assert context['fileFormat'] == {
        'in': './tests/testfiles/{inFileName}.txt',
        'out': './tests/testfiles/out/{outFileName}.txt',
        'encodingIn': '{encIn}',
        'encodingOut': '{encOut}'}

    with open('./tests/testfiles/out/outsubst.txt',
              encoding='utf-32') as outfile:
        outcontents = outfile.read()

    assert outcontents == """this v1 is line 1
this is line 2 v2
this is line 3
this v3 is  v4 line 4
this !£$% * is v5 line 5
"""
