"""fileformatyaml.py unit tests."""
import os
import shutil
import ruamel.yaml as yaml
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformatyaml as fileformat
import pytest


def test_fileformatyaml_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "fileFormatYaml not found in the pypyr context.")


def test_fileformatyaml_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatYaml': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatYaml']['in'] must have "
                                   "a value for pypyr.steps.fileformatyaml.")


def test_fileformatyaml_pass_no_substitutions():
    """Relative path to file should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileFormatYaml': {'in': './tests/testfiles/test.yaml',
                           'out': './tests/testfiles/out/out.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/test.yaml',
        'out': './tests/testfiles/out/out.yaml'}

    with open('./tests/testfiles/out/out.yaml') as outfile:
        yaml_loader = yaml.YAML(typ='rt', pure=True)
        outcontents = yaml_loader.load(outfile)

    assert len(outcontents) == 3
    assert outcontents['key'] == 'value1 !£$%# *'
    assert outcontents['key2'] == 'blah'
    assert outcontents['key3'] == ['l1',
                                   '!£$% *',
                                   'l2',
                                   [
                                       'l31',
                                       {'l32': ['l321', 'l322']}
                                   ]
                                   ]

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/out.yaml')


def test_fileformatyaml_pass_with_substitutions():
    """Relative path to file should succeed.

    Strictly speaking not a unit test.
    """
    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatYaml': {'in': './tests/testfiles/testsubst.yaml',
                           'out': './tests/testfiles/out/outsubst.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/testsubst.yaml',
        'out': './tests/testfiles/out/outsubst.yaml'}

    with open('./tests/testfiles/out/outsubst.yaml') as outfile:
        yaml_loader = yaml.YAML(typ='rt', pure=True)
        outcontents = yaml_loader.load(outfile)

    expected = {
        'key': 'v1value1 !£$%# *',
        'key2v2': 'blah',
        # there is a comment here
        'key3': [
            'l1',
            # and another
            '!£$% * v3',
            'l2', ['l31v4',
                   {'l32': ['l321',
                            'l322v5']
                    }
                   ]
        ]
    }

    assert outcontents == expected

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.yaml')


def test_fileformatyaml_edit_with_substitutions():
    """Relative path to file should succeed, with no out meaning edit.

    Strictly speaking not a unit test.
    """
    shutil.copyfile('./tests/testfiles/testsubst.yaml',
                    './tests/testfiles/out/edittestsubst.yaml')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatYaml': {'in': './tests/testfiles/out/edittestsubst.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/out/edittestsubst.yaml'}

    with open('./tests/testfiles/out/edittestsubst.yaml') as outfile:
        yaml_loader = yaml.YAML(typ='rt', pure=True)
        outcontents = yaml_loader.load(outfile)

    expected = {
        'key': 'v1value1 !£$%# *',
        'key2v2': 'blah',
        # there is a comment here
        'key3': [
            'l1',
            # and another
            '!£$% * v3',
            'l2', ['l31v4',
                   {'l32': ['l321',
                            'l322v5']
                    }
                   ]
        ]
    }

    assert outcontents == expected

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/edittestsubst.yaml')


def test_fileformatyaml_pass_with_path_substitutions():
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
        'fileFormatYaml': {'in': './tests/testfiles/{pathIn}.yaml',
                           'out': './tests/testfiles/out/{pathOut}.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 8, "context should have 8 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/{pathIn}.yaml',
        'out': './tests/testfiles/out/{pathOut}.yaml'}

    with open('./tests/testfiles/out/outsubst.yaml') as outfile:
        yaml_loader = yaml.YAML(typ='rt', pure=True)
        outcontents = yaml_loader.load(outfile)

    expected = {
        'key': 'v1value1 !£$%# *',
        'key2v2': 'blah',
        # there is a comment here
        'key3': [
            'l1',
            # and another
            '!£$% * v3',
            'l2', ['l31v4',
                   {'l32': ['l321',
                            'l322v5']
                    }
                   ]
        ]
    }

    assert outcontents == expected

    # atrociously lazy test clean-up
    os.remove('./tests/testfiles/out/outsubst.yaml')

# --------------------------- teardown ---------------------------------------


def teardown_module(module):
    """Teardown."""
    os.rmdir('./tests/testfiles/out/')
