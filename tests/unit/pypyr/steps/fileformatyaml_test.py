"""fileformatyaml.py unit tests."""
import os
from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformatyaml as fileformat
import pytest
import ruamel.yaml as yaml


def test_fileformatyaml_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fileFormatYamlIn'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.fileformatyaml.\",)")


def test_fileformatyaml_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatYamlIn': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fileFormatYamlIn'] must have "
        "a value for pypyr.steps.fileformatyaml.\",)")


def test_fileformatyaml_no_outpath_raises():
    """None out path raises."""
    context = Context({
        'fileFormatYamlIn': 'blah',
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert repr(err_info.value) == (
        "KeyNotInContextError(\"context['fileFormatYamlOut'] "
        "doesn't exist. It must exist for "
        "pypyr.steps.fileformatyaml.\",)")


def test_fileformatyaml_empty_outpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatYamlIn': 'blah',
        'fileFormatYamlOut': None})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert repr(err_info.value) == (
        "KeyInContextHasNoValueError(\"context['fileFormatYamlOut'] must have "
        "a value for pypyr.steps.fileformatyaml.\",)")


def test_fileformatyaml_pass_no_substitutions():
    """Relative path to file should succeed.

     Strictly speaking not a unit test.
    """
    context = Context({
        'ok1': 'ov1',
        'fileFormatYamlIn': './tests/testfiles/test.yaml',
        'fileFormatYamlOut': './tests/testfiles/out/out.yaml'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 3, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatYamlIn'] == './tests/testfiles/test.yaml'
    assert context['fileFormatYamlOut'] == './tests/testfiles/out/out.yaml'

    with open('./tests/testfiles/out/out.yaml') as outfile:
        outcontents = yaml.load(outfile, Loader=yaml.RoundTripLoader)

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
        'fileFormatYamlIn': './tests/testfiles/testsubst.yaml',
        'fileFormatYamlOut': './tests/testfiles/out/outsubst.yaml'})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 7, "context should have 7 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYamlIn'] == './tests/testfiles/testsubst.yaml'
    assert context['fileFormatYamlOut'] == ('./tests/testfiles/out/'
                                            'outsubst.yaml')

    with open('./tests/testfiles/out/outsubst.yaml') as outfile:
        outcontents = yaml.load(outfile, Loader=yaml.RoundTripLoader)

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


def teardown_module(module):
    """Teardown"""
    os.rmdir('./tests/testfiles/out/')
