"""fileformat.py unit tests.

The bulk of coverage is in tests/integration/pypyr/utils/filesystem_int_test.py
"""
import io
from unittest.mock import mock_open

import pytest
import pypyr.utils.filesystem as filesystem

# region FileRewriter


def test_filerewriter_abstract():
    """Can't instantiate FileRewriter."""
    with pytest.raises(TypeError):
        filesystem.FileRewriter('blah')


def test_filerewriter_in_to_out_abstract():
    """Can't invoke in_to_out on abstract base."""
    class MyRewriter(filesystem.FileRewriter):
        def in_to_out(self, in1):
            super().in_to_out('blah', 'blah')

    x = MyRewriter('blahinit')

    with pytest.raises(NotImplementedError):
        x.in_to_out('blah')
# endregion FileRewriter

# region ObjectRepresenter


def test_objectrepresenter_abstract():
    """Can't instantiate ObjectRepresenter."""
    with pytest.raises(TypeError):
        filesystem.ObjectRepresenter()


def test_object_representer_abc_methods():
    """Abstract methods do nothing and mode defaults."""
    class MyRepresenter(filesystem.ObjectRepresenter):
        def load(self, file):
            super().load(file)

        def dump(self, file, payload):
            super().dump(file, payload)

    x = MyRepresenter()
    x.load(None)
    x.dump(None, None)

    # defaults for mode is text read or write.
    assert x.read_mode == 'rt'
    assert x.write_mode == 'wt'


def test_json_representer():
    """Json representer load and dump payload."""
    representer = filesystem.JsonRepresenter()

    assert representer.read_mode == 'rt'
    assert representer.write_mode == 'wt'

    in_json = '{"a": "b", "c": [1,2,true]}'
    obj = representer.load(mock_open(read_data=in_json)())

    assert obj == {'a': 'b', 'c': [1, 2, True]}

    with io.StringIO() as out_text:
        mock_output = mock_open()
        mock_output.return_value.write.side_effect = out_text.write
        representer.dump(mock_output(), obj)

        assert out_text.getvalue() == ('{\n'
                                       '  "a": "b",\n'
                                       '  "c": [\n'
                                       '    1,\n'
                                       '    2,\n'
                                       '    true\n'
                                       '  ]\n'
                                       '}')


def test_toml_representer():
    """Toml representer load and dump payload."""
    representer = filesystem.TomlRepresenter()

    assert representer.read_mode == 'rb'
    assert representer.write_mode == 'wb'

    in_toml = b'a = "b"\nc = [1,2,true]'
    with mock_open(read_data=in_toml)() as f:
        obj = representer.load(f)

    assert obj == {'a': 'b', 'c': [1, 2, True]}

    with io.BytesIO() as out_bytes:
        mock_output = mock_open()
        mock_output.return_value.write.side_effect = out_bytes.write
        representer.dump(mock_output(), obj)

        assert out_bytes.getvalue().decode() == ('a = "b"\n'
                                                 'c = [\n'
                                                 '    1,\n'
                                                 '    2,\n'
                                                 '    true,\n'
                                                 ']\n')


def test_yaml_representer():
    """Yaml representer load and dump payload."""
    representer = filesystem.YamlRepresenter()

    assert representer.read_mode == 'rt'
    assert representer.write_mode == 'wt'

    in_yaml = ('a: b\n'
               'c:\n'
               '  - 1\n'
               '  - 2\n'
               '  - True\n')
    obj = representer.load(mock_open(read_data=in_yaml)())

    assert obj == {'a': 'b', 'c': [1, 2, True]}

    with io.StringIO() as out_text:
        mock_output = mock_open()
        mock_output.return_value.write.side_effect = out_text.write
        representer.dump(mock_output(), obj)

        assert out_text.getvalue() == ('a: b\n'
                                       'c:\n'
                                       '  - 1\n'
                                       '  - 2\n'
                                       '  - true\n')

# endregion ObjectRepresenter

# region is_same_file


def test_is_same_file_none():
    """Empty paths not same."""
    assert not filesystem.is_same_file(None, '')


# endregion is_same_file
