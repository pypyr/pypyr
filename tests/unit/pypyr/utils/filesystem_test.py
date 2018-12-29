"""fileformat.py unit tests."""
import io
import pytest
from unittest.mock import mock_open
import pypyr.utils.filesystem as filesystem

# ------------------------ FileRewriter ---------------------------------------


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
# ------------------------ END of FileRewriter --------------------------------

# ------------------------ ObjectRepresenter ----------------------------------


def test_objectrepresenter_abstract():
    """Can't instantiate ObjectRepresenter."""
    with pytest.raises(TypeError):
        filesystem.ObjectRepresenter()


def test_object_representer_abc_methods():
    """Abstract methods do nothing."""
    class MyRepresenter(filesystem.ObjectRepresenter):
        def load(self, file):
            super().load(file)

        def dump(self, file, payload):
            super().dump(file, payload)

    x = MyRepresenter()
    x.load(None)
    x.dump(None, None)


def test_json_representer():
    """Json representer load and dump payload."""
    representer = filesystem.JsonRepresenter()

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


def test_yaml_representer():
    """Yaml representer load and dump payload."""
    representer = filesystem.YamlRepresenter()

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

# ------------------------ END ObjectRepresenter ------------------------------

# ------------------------ is_same_file --------------------------------------


def test_is_same_file_none():
    """Empty paths not same."""
    assert not filesystem.is_same_file(None, '')


# ------------------------ END is_same_file -----------------------------------
