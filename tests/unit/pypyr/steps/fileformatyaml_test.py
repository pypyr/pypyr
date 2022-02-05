"""fileformatyaml.py unit tests."""
from unittest.mock import patch

import pytest
import ruamel.yaml as yaml

from pypyr.context import Context
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
import pypyr.steps.fileformatyaml as fileformat


def test_fileformatyaml_no_inpath_raises():
    """None in path raises."""
    context = Context({
        'k1': 'v1'})

    with pytest.raises(KeyNotInContextError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == (
        "context['fileFormatYaml'] doesn't exist. "
        "It must exist for pypyr.steps.fileformatyaml.")


def test_fileformatyaml_empty_inpath_raises():
    """Empty in path raises."""
    context = Context({
        'fileFormatYaml': {'in': None}})

    with pytest.raises(KeyInContextHasNoValueError) as err_info:
        fileformat.run_step(context)

    assert str(err_info.value) == ("context['fileFormatYaml']['in'] must have "
                                   "a value for pypyr.steps.fileformatyaml.")


def test_fileformatyaml_pass_no_substitutions(fs):
    """Relative path to file should succeed."""
    in_path = './tests/testfiles/test.yaml'
    fs.create_file(in_path, contents="""key: value1 !£$%# *
key2: blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% *'
- l2
- - l31
  - l32:
    - l321
    - l322
    """)

    context = Context({
        'ok1': 'ov1',
        'fileFormatYaml': {'in': in_path,
                           'out': './tests/testfiles/out/out.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 2, "context should have 2 items"
    assert context['ok1'] == 'ov1'
    assert context['fileFormatYaml'] == {
        'in': in_path,
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


def test_fileformatyaml_pass_with_substitutions(fs):
    """Relative path to file should succeed with substitutions."""
    in_path = './tests/testfiles/testsubst.yaml'
    fs.create_file(in_path, contents="""key: "{k1}value1 !£$%# *"
"key2{k2}": blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% * {k3}'
- l2
- - l31{k4}
  - l32:
    - l321
    - l322{k5}
""")

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatYaml': {'in': in_path,
                           'out': './tests/testfiles/out/outsubst.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': in_path,
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


def test_fileformatyaml_edit_with_substitutions(fs):
    """Relative path to file should succeed, with no out meaning edit."""
    in_path = './tests/testfiles/out/edittestsubst.yaml'
    fs.create_file(in_path, contents="""key: "{k1}value1 !£$%# *"
"key2{k2}": blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% * {k3}'
- l2
- - l31{k4}
  - l32:
    - l321
    - l322{k5}
""")

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'fileFormatYaml': {'in': in_path}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 6, "context should have 6 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': in_path}

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


def test_fileformatyaml_pass_with_path_substitutions(fs):
    """Relative path to file should succeed with path substitutions."""
    in_path = './tests/testfiles/testsubst.yaml'
    fs.create_file(in_path, contents="""key: "{k1}value1 !£$%# *"
"key2{k2}": blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% * {k3}'
- l2
- - l31{k4}
  - l32:
    - l321
    - l322{k5}
""")

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


def test_fileformatyaml_pass_with_encoding(fs):
    """Relative path to file should succeed with encoding."""
    in_path = './tests/testfiles/testsubst.yaml'
    fs.create_file(in_path, contents="""key: "{k1}value1 !£$%# *"
"key2{k2}": blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% * {k3}'
- l2
- - l31{k4}
  - l32:
    - l321
    - l322{k5}
""", encoding='utf-16')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'enc': 'utf-16',
        'pathIn': 'testsubst',
        'pathOut': 'outsubst',
        'fileFormatYaml': {'in': './tests/testfiles/{pathIn}.yaml',
                           'out': './tests/testfiles/out/{pathOut}.yaml',
                           'encoding': '{enc}'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/{pathIn}.yaml',
        'out': './tests/testfiles/out/{pathOut}.yaml',
        'encoding': '{enc}'}

    with open('./tests/testfiles/out/outsubst.yaml',
              encoding='utf-16') as outfile:
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


@patch('pypyr.config.config.default_encoding', new='utf-16')
def test_fileformatyaml_pass_with_encoding_from_config(fs):
    """Relative path to file should succeed with path substitutions."""
    in_path = './tests/testfiles/testsubst.yaml'
    fs.create_file(in_path, contents="""key: "{k1}value1 !£$%# *"
"key2{k2}": blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% * {k3}'
- l2
- - l31{k4}
  - l32:
    - l321
    - l322{k5}
""", encoding='utf-16')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'enc': 'utf-16',
        'pathIn': 'testsubst',
        'pathOut': 'outsubst',
        'fileFormatYaml': {'in': './tests/testfiles/{pathIn}.yaml',
                           'out': './tests/testfiles/out/{pathOut}.yaml'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/{pathIn}.yaml',
        'out': './tests/testfiles/out/{pathOut}.yaml'}

    with open('./tests/testfiles/out/outsubst.yaml',
              encoding='utf-16') as outfile:
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


def test_fileformatyaml_pass_with_encoding_ut32(fs):
    """Relative path to file should succeed with encoding."""
    in_path = './tests/testfiles/testsubst.yaml'
    fs.create_file(in_path, contents="""key: "{k1}value1 !£$%# *"
"key2{k2}": blah
# there is a comment here
key3:
- l1
  # and another
- '!£$% * {k3}'
- l2
- - l31{k4}
  - l32:
    - l321
    - l322{k5}
""", encoding='utf-32')

    context = Context({
        'k1': 'v1',
        'k2': 'v2',
        'k3': 'v3',
        'k4': 'v4',
        'k5': 'v5',
        'enc': 'utf-32',
        'pathIn': 'testsubst',
        'pathOut': 'outsubst',
        'fileFormatYaml': {'in': './tests/testfiles/{pathIn}.yaml',
                           'out': './tests/testfiles/out/{pathOut}.yaml',
                           'encoding': '{enc}'}})

    fileformat.run_step(context)

    assert context, "context shouldn't be None"
    assert len(context) == 9, "context should have 9 items"
    assert context['k1'] == 'v1'
    assert context['fileFormatYaml'] == {
        'in': './tests/testfiles/{pathIn}.yaml',
        'out': './tests/testfiles/out/{pathOut}.yaml',
        'encoding': '{enc}'}

    with open('./tests/testfiles/out/outsubst.yaml',
              encoding='utf-32') as outfile:
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
