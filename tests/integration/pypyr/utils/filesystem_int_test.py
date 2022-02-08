"""fileformat.py integration tests."""
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import call, patch

import pypyr.utils.filesystem as filesystem
import pytest
from pypyr.errors import Error
# region setup/teardown/fixtures
from tests.common.utils import patch_logger


@pytest.fixture(scope="module")
def temp_dir():
    """Make tmp dir in testfiles/out."""
    # runs at start of module
    os.makedirs('./tests/testfiles/out/', exist_ok=True)
    tmp_dir = tempfile.TemporaryDirectory(dir='./tests/testfiles/out/')
    yield Path(tmp_dir.name)
    # runs when module done
    tmp_dir.cleanup()
    os.rmdir('./tests/testfiles/out/')


@pytest.fixture
def temp_file_creator(temp_dir):
    """Create a function that makes a temp file in a fixture."""
    temp_files = []

    def create_temp_file():
        """Create a temp file for each function invocation."""
        # close file handle to allow other code to use file on windows
        with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as tmp:
            p = Path(tmp.name)

        temp_files.append(p)
        return p

    yield create_temp_file

    # this runs after the decorated test goes out of scope
    for file in temp_files:
        try:
            # can't use missing_ok=True until py 3.8 the min ver.
            file.unlink()
        except FileNotFoundError:
            # just clean-up, if file already been removed no probs
            pass

# endregion setup/teardown/fixtures

# region FileRewriter


class ArbRewriter(filesystem.FileRewriter):
    """Derived FileRewriter useful for capturing test inputs."""

    def __init__(self, formatter):
        """Initialize calls list."""
        self.in_out_calls = []
        self.in_out_calls_paths = []
        super().__init__(formatter)

    def in_to_out(self, in_path, out_path=None):
        """Don't do much except log inputs."""
        self.in_out_calls.append({'in': in_path, 'out': out_path})
        out_obj = Path(out_path).resolve() if out_path else None
        self.in_out_calls_paths.append({'in': Path(in_path).resolve(),
                                        'out': out_obj})

    def assert_in_to_out_call(self, in_path, out_path):
        """Assert that the in/out pair exists in the call list."""
        assert (any(dict for dict in self.in_out_calls
                    if dict['in'] == in_path
                    and dict['out'] == out_path))

    def assert_in_to_out_call_path(self, in_path, out_path):
        """Assert that the in/out paths exists in the call list.

        Args:
            in_path: Pathlib Path. Uses .resolve() to normalize path.
            out_path: Pathlib Path. Uses .resolve() to normalize path.

        Returns:
            None.

        Raises:
            AssertionError if no match found.

        """
        in_resolved = Path(in_path).resolve() if in_path else None
        out_resolved = Path(out_path).resolve() if out_path else None
        assert (any(dict for dict in self.in_out_calls_paths
                    if dict['in'] == in_resolved
                    and dict['out'] == out_resolved))

    def assert_in_to_out_call_count(self, count):
        """Assert that the number of in_to_out calls is count."""
        assert len(self.in_out_calls) == count


def test_arbwriter_assert_in_to_out_call_exists():
    """Arb Rewriter asserts should work as advertized."""
    arb = ArbRewriter('formatter')
    arb.in_to_out('1', '2')
    arb.in_to_out('3', '4')

    arb.assert_in_to_out_call('1', '2')
    arb.assert_in_to_out_call('3', '4')
    arb.assert_in_to_out_call_path(Path('1'), Path('2'))
    arb.assert_in_to_out_call_path(Path('3'), Path('4'))
    arb.assert_in_to_out_call_count(2)

    with pytest.raises(AssertionError):
        arb.assert_in_to_out_call('5', '6')


def test_filerewriter_files_in_to_out_no_in_found_no_out():
    """Files in to out does nothing when in glob finds nothing, no outpath."""
    rewriter = ArbRewriter("formatter")

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out('./arb/*')

    assert mock_logger_info.mock_calls == [
        call("./arb/* found no files")]

    assert not rewriter.in_out_calls


def test_filerewriter_files_in_to_out_no_in_found_with_out():
    """Files in to out does nothing when in glob finds nothing, with out."""
    rewriter = ArbRewriter("formatter")

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out('./arb/*', './arb2/*')

    assert mock_logger_info.mock_calls == [
        call("./arb/* found no files")]

    assert not rewriter.in_out_calls


def test_filerewriter_files_in_to_out_1_to_1_str(temp_dir,
                                                 temp_file_creator):
    """Files in to out invokes file_in_to_out for each file on str input."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()
    out = temp_dir.joinpath('outfile')

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(str(file1), str(out))

    assert mock_logger_info.mock_calls == [
        call(f"read {file1}, formatted and wrote 1 file(s) to {out}")]

    assert rewriter.in_out_calls == [{'in': file1, 'out': out}]


def test_filerewriter_files_in_to_out_1_to_1_path(temp_dir,
                                                  temp_file_creator):
    """Files in to out invokes file_in_to_out for each file on path input."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()
    out = temp_dir.joinpath('outfile')

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(file1, out)

    assert mock_logger_info.mock_calls == [
        call(f"read {file1}, formatted and wrote 1 file(s) to {out}")]

    assert rewriter.in_out_calls == [{'in': file1, 'out': out}]


def test_filerewriter_files_in_to_out_3_to_1(temp_dir,
                                             temp_file_creator):
    """Files in to out can't write multiple ins to 1 out."""
    rewriter = ArbRewriter("formatter")

    temp_file_creator()
    temp_file_creator()
    temp_file_creator()

    in_glob = temp_dir.joinpath('*')
    out = temp_dir.joinpath('outfile')

    with pytest.raises(Error) as err:
        rewriter.files_in_to_out(in_glob, out)

    assert str(err.value) == (
        f'{in_glob} resolves to 3 files, but you '
        f'specified only a single file as out {out}. If the outpath is meant '
        'to be a directory, put a / at the end.')

    assert not rewriter.in_out_calls


def test_filerewriter_files_in_to_out_edit_dir_slash(temp_dir,
                                                     temp_file_creator):
    """Files in to out edits when out existing dir shown by /."""
    rewriter = ArbRewriter("formatter")

    temp_file_creator()
    temp_file_creator()

    in_path = temp_dir.joinpath('*')
    out = str(temp_dir) + os.sep

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(in_path, out)

    assert mock_logger_info.mock_calls == [
        call(f"read {in_path}, formatted and wrote 2 file(s) to {out}")]

    rewriter.assert_in_to_out_call_count(2)


def test_filerewriter_files_in_to_out_dir_slash_create(temp_dir,
                                                       temp_file_creator):
    """Files in to out when out dir shown by / creates dir."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()
    file2 = temp_file_creator()

    in_path = temp_dir.joinpath("*")
    out = str(temp_dir.joinpath('sub')) + os.sep

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(in_path, out)

    assert mock_logger_info.mock_calls == [
        call(f"read {in_path}, formatted and wrote 2 file(s) to {out}")]

    path_out = Path(out)
    # out/sub exists
    assert path_out.is_dir()
    rewriter.assert_in_to_out_call_count(2)
    # outfile created with same name as in-file in out/sub dir
    rewriter.assert_in_to_out_call_path(file1, path_out.joinpath(file1.name))
    rewriter.assert_in_to_out_call_path(file2, path_out.joinpath(file2.name))


def test_filerewriter_files_in_to_out_edit_dir_no_slash(temp_dir,
                                                        temp_file_creator):
    """Files in to out edits when out existing dir, without trailing slash."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(file1, temp_dir)

    assert mock_logger_info.mock_calls == [
        call(f"read {file1}, formatted and wrote 1 file(s) to {temp_dir}")]

    rewriter.assert_in_to_out_call_count(1)
    rewriter.assert_in_to_out_call_path(Path(file1),
                                        temp_dir.joinpath(file1.name))


def test_filerewriter_files_in_to_out_no_out(temp_file_creator):
    """Files in to out with no out edits in place."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(file1)

    assert mock_logger_info.mock_calls == [
        call(f"edited & wrote 1 file(s) at {file1}")]

    rewriter.assert_in_to_out_call_count(1)
    rewriter.assert_in_to_out_call_path(Path(file1), None)


def test_filerewriter_files_in_to_out_in_glob_no_out(temp_dir,
                                                     temp_file_creator):
    """Files in to out with in glob and no out edits in place."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()
    file2 = temp_file_creator()
    file3 = temp_file_creator()

    in_glob = temp_dir.joinpath('*')

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(in_glob)

    assert mock_logger_info.mock_calls == [
        call(f"edited & wrote 3 file(s) at {in_glob}")]

    rewriter.assert_in_to_out_call_count(3)
    rewriter.assert_in_to_out_call_path(file1, None)
    rewriter.assert_in_to_out_call_path(file2, None)
    rewriter.assert_in_to_out_call_path(file3, None)


def test_filerewriter_files_in_to_out_in_list_no_out(temp_file_creator):
    """Files in to out with in list and no out edits in place."""
    rewriter = ArbRewriter("formatter")

    file1 = temp_file_creator()
    file2 = temp_file_creator()
    file3 = temp_file_creator()

    in_list = [file1, str(file2), file3]

    with patch_logger(
            'pypyr.utils.filesystem', logging.INFO
    ) as mock_logger_info:
        rewriter.files_in_to_out(in_list)

    assert mock_logger_info.mock_calls == [
        call(f"edited & wrote 3 file(s) at {in_list}")]

    rewriter.assert_in_to_out_call_count(3)
    rewriter.assert_in_to_out_call_path(file1, None)
    rewriter.assert_in_to_out_call_path(file2, None)
    rewriter.assert_in_to_out_call_path(file3, None)

# endregion FileRewriter

# region ObjectRewriter


class ArbRepresenter(filesystem.ObjectRepresenter):
    """Test representer."""

    def __init__(self, is_binary=False):
        """Initialize me."""
        super().__init__(is_binary)
        self.load_payload = None
        self.dump_payload = None
        self.load_call_count = 0
        self.dump_call_count = 0

    def load(self, file):
        """Get payload from file."""
        self.load_payload = file.read()
        self.load_call_count += 1
        return self.load_payload

    def dump(self, file, payload):
        """Write payload to file."""
        file.write(payload)
        self.dump_payload = payload
        self.dump_call_count += 1


def get_arb_formatted(input):
    """Arbitrary formatter takes a string and returns a string."""
    return f'X{input}X'


def get_binary_formatted(input):
    """Arbitrary formatter takes bytes and concats some bytes."""
    return b'X' + input + b'X'


def get_arb_formatted_iter(input):
    """Arbitrary formatter takes an iterable and returns an iterable."""
    for item in input:
        yield f'X{item}X'


def test_objectrewriter_in_to_out_str(temp_dir, temp_file_creator):
    """Object Rewriter writes single in to out str."""
    representer = ArbRepresenter()
    rewriter = filesystem.ObjectRewriter(get_arb_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')
    out_str = str(temp_dir.joinpath('sub', 'filename'))

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(str(path_in), out_str)

    assert representer.load_payload == 'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == 'XyyyX'
    assert representer.dump_call_count == 1

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call(f"opening destination file for writing: {out_str}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'yyy'
    path_out = Path(out_str)
    assert path_out.is_file()
    assert path_out.read_text() == 'XyyyX'


def test_objectrewriter_in_to_out_path(temp_dir, temp_file_creator):
    """Object Rewriter writes single in to out path object."""
    representer = ArbRepresenter()
    rewriter = filesystem.ObjectRewriter(get_arb_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')
    path_out = temp_dir.joinpath('sub', 'filename')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(path_in, path_out)

    assert representer.load_payload == 'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == 'XyyyX'
    assert representer.dump_call_count == 1

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call(f"opening destination file for writing: {path_out}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'yyy'
    assert path_out.is_file()
    assert path_out.read_text() == 'XyyyX'


def test_objectrewriter_in_to_out_path_binary(temp_dir, temp_file_creator):
    """Object Rewriter writes single in to out path object in binary mode."""
    representer = ArbRepresenter(True)
    rewriter = filesystem.ObjectRewriter(get_binary_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')
    path_out = temp_dir.joinpath('sub', 'filename')

    rewriter.in_to_out(path_in, path_out)

    assert representer.load_payload == b'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == b'XyyyX'
    assert representer.dump_call_count == 1

    assert path_in.is_file()
    assert path_in.read_text() == 'yyy'
    assert path_out.is_file()
    assert path_out.read_text() == 'XyyyX'


def test_objectrewriter_in_to_out_no_out_path(temp_file_creator):
    """Object Rewriter in place edit with path object."""
    representer = ArbRepresenter()
    rewriter = filesystem.ObjectRewriter(get_arb_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(path_in, None)

    assert representer.load_payload == 'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == 'XyyyX'
    assert representer.dump_call_count == 1

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call("opening temp file for writing..."),
        call(f"moving temp file to: {path_in}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'


def test_objectrewriter_in_to_out_no_out_path_binary(temp_file_creator):
    """Object Rewriter in place edit with path object in binary mode."""
    representer = ArbRepresenter(True)
    rewriter = filesystem.ObjectRewriter(get_binary_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    rewriter.in_to_out(path_in, None)

    assert representer.load_payload == b'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == b'XyyyX'
    assert representer.dump_call_count == 1

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'


def test_objectrewriter_in_to_out_no_out_str(temp_file_creator):
    """Object Rewriter in place edit with str object."""
    representer = ArbRepresenter()
    rewriter = filesystem.ObjectRewriter(get_arb_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(str(path_in), None)

    assert representer.load_payload == 'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == 'XyyyX'
    assert representer.dump_call_count == 1

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call("opening temp file for writing..."),
        call(f"moving temp file to: {path_in}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'


def test_objectrewriter_in_to_out_same_path(temp_file_creator):
    """Object Rewriter in place edit with path object."""
    representer = ArbRepresenter()
    rewriter = filesystem.ObjectRewriter(get_arb_formatted,
                                         representer)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    str_out = os.path.relpath(path_in)

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(path_in, str_out)

    assert representer.load_payload == 'yyy'
    assert representer.load_call_count == 1
    assert representer.dump_payload == 'XyyyX'
    assert representer.dump_call_count == 1

    assert mock_logger_debug.mock_calls == [
        call("in path and out path are the same file. writing to temp "
             "file and then replacing in path with the temp file."),
        call(f"opening source file: {path_in}"),
        call("opening temp file for writing..."),
        call(f"moving temp file to: {path_in}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'
# endregion ObjectRewriter

# region StreamRewriter


def test_streamrewriter_in_to_out_path(temp_dir, temp_file_creator):
    """Stream Rewriter writes single in to out path object."""
    rewriter = filesystem.StreamRewriter(get_arb_formatted_iter)

    path_in = temp_file_creator()
    path_in.write_text('yyy')
    path_out = temp_dir.joinpath('sub', 'filename')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(path_in, path_out)

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call(f"opening destination file for writing: {path_out}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'yyy'
    assert path_out.is_file()
    assert path_out.read_text() == 'XyyyX'


def test_streamrewriter_in_to_out_str(temp_dir, temp_file_creator):
    """Stream Rewriter writes single in to out path object."""
    rewriter = filesystem.StreamRewriter(get_arb_formatted_iter)

    path_in = temp_file_creator()
    path_in.write_text('yyy')
    path_out = temp_dir.joinpath('sub', 'filename')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(str(path_in), str(path_out))

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call(f"opening destination file for writing: {path_out}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'yyy'
    assert path_out.is_file()
    assert path_out.read_text() == 'XyyyX'


def test_streamrewriter_in_to_out_no_out_path(temp_file_creator):
    """Stream Rewriter in place edit with path object."""
    rewriter = filesystem.StreamRewriter(get_arb_formatted_iter)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(path_in, None)

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call("opening temp file for writing..."),
        call(f"moving temp file to: {path_in}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'


def test_streamrewriter_in_to_out_no_out_str(temp_file_creator):
    """Stream Rewriter in place edit with str object."""
    rewriter = filesystem.StreamRewriter(get_arb_formatted_iter)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(str(path_in), None)

    assert mock_logger_debug.mock_calls == [
        call(f"opening source file: {path_in}"),
        call("opening temp file for writing..."),
        call(f"moving temp file to: {path_in}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'


def test_streamrewriter_in_to_out_same_path(temp_file_creator):
    """Stream Rewriter in place edit with same path."""
    rewriter = filesystem.StreamRewriter(get_arb_formatted_iter)

    path_in = temp_file_creator()
    path_in.write_text('yyy')

    str_out = os.path.relpath(path_in)

    with patch_logger(
            'pypyr.utils.filesystem', logging.DEBUG
    ) as mock_logger_debug:
        rewriter.in_to_out(str(path_in), str_out)

    assert mock_logger_debug.mock_calls == [
        call("in path and out path are the same file. writing to temp "
             "file and then replacing in path with the temp file."),
        call(f"opening source file: {path_in}"),
        call("opening temp file for writing..."),
        call(f"moving temp file to: {path_in}")]

    assert path_in.is_file()
    assert path_in.read_text() == 'XyyyX'

# endregion StreamRewriter

# region ObjectRepresenter


def test_jsonrepresenter_loads():
    """Json Representer loads."""
    representer = filesystem.JsonRepresenter()
    with open('./tests/testfiles/test.json', representer.read_mode) as file:
        obj = representer.load(file)

    assert obj
    assert obj['key1'] == 'value1'
    assert obj['key2'] == 'value2'
    assert obj['key3'] == 'value3'


def test_jsonrepresenter_dumps(temp_file_creator):
    """Json Representer dumps."""
    payload = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': [0, 1, 2]
    }
    representer = filesystem.JsonRepresenter()
    file_path = temp_file_creator()
    with open(file_path, representer.write_mode) as file:
        representer.dump(file, payload)

    assert file_path.read_text() == ('{\n'
                                     '  "key1": "value1",\n'
                                     '  "key2": "value2",\n'
                                     '  "key3": [\n'
                                     '    0,\n'
                                     '    1,\n'
                                     '    2\n'
                                     '  ]\n'
                                     '}')


def test_yamlrepresenter_loads():
    """Yaml Representer loads."""
    representer = filesystem.YamlRepresenter()
    with open('./tests/testfiles/test.yaml',
              representer.read_mode,
              encoding='utf-8') as file:
        obj = representer.load(file)

    assert obj
    assert obj == {'key': 'value1 !£$%# *',
                   'key2': 'blah',
                   'key3': ['l1',
                            '!£$% *',
                            'l2',
                            [
                                'l31',
                                {'l32': ['l321', 'l322']}]
                            ]}


def test_yamlrepresenter_dumps(temp_file_creator):
    """Yaml Representer dumps."""
    payload = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': [0, 1, 2]
    }
    representer = filesystem.YamlRepresenter()
    file_path = temp_file_creator()
    with open(file_path, representer.write_mode) as file:
        representer.dump(file, payload)

    assert file_path.read_text() == ('key1: value1\n'
                                     'key2: value2\n'
                                     'key3:\n'
                                     '  - 0\n'
                                     '  - 1\n'
                                     '  - 2\n')
# endregion ObjectRepresenter

# region ensure_dir


def test_ensure_dir(temp_dir):
    """Ensure dir creates parent path with string input."""
    path = temp_dir.joinpath('sub1', 'sub2')

    filesystem.ensure_dir(str(path))
    assert temp_dir.joinpath('sub1').is_dir()


def test_ensure_dir_path(temp_dir):
    """Ensure dir creates parent path with path input."""
    path = temp_dir.joinpath('sub1', 'sub2')

    filesystem.ensure_dir(path)
    assert temp_dir.joinpath('sub1').is_dir()

# endregion ensure_dir

# region get_glob


def assert_list_of_paths_equal(obj, other):
    """Cross platform compare of list of paths."""
    assert set([Path(p) for p in obj]) == set([Path(p) for p in other])


def test_get_glob_str():
    """Glob takes strings."""
    paths = filesystem.get_glob('./tests/testfiles/t???.txt')

    assert_list_of_paths_equal(paths, ['./tests/testfiles/test.txt'])


def test_get_glob_path():
    """Glob takes paths."""
    paths = filesystem.get_glob(Path('./tests/testfiles/t???.txt'))
    assert_list_of_paths_equal(paths, ['./tests/testfiles/test.txt'])


def test_get_glob_list():
    """Glob takes list of str and paths."""
    paths = filesystem.get_glob([Path('./tests/testfiles/t???.txt'),
                                 './tests/testfiles/a*.py'])
    assert_list_of_paths_equal(paths, ['tests/testfiles/test.txt',
                                       './tests/testfiles/arb.py'])


def test_get_glob_chain():
    """Multiple results from iterable input chains into single output."""
    paths = filesystem.get_glob([Path('./tests/testfiles/glob/a*.1'),
                                 './tests/testfiles/glob/a*2',
                                 './tests/testfiles/glob/a*.3'])
    assert_list_of_paths_equal(paths,
                               ['tests/testfiles/glob/arb.1.1',
                                'tests/testfiles/glob/arb.1',
                                './tests/testfiles/glob/arb.2',
                                './tests/testfiles/glob/arb.2.2',
                                './tests/testfiles/glob/arb.3'])


def test_get_glob_recurse():
    """Double asterix recurses. Also returns directories."""
    paths = filesystem.get_glob([Path('./tests/testfiles/glob/**/a*.1'),
                                 './tests/testfiles/glob/**/a*2',
                                 './tests/testfiles/glob/**/a*.3'])

    assert_list_of_paths_equal(paths,
                               ['tests/testfiles/glob/arb.1.1',
                                'tests/testfiles/glob/arb.1',
                                'tests/testfiles/glob/sub/asub.1',
                                'tests/testfiles/glob/sub/arbsub.1',
                                './tests/testfiles/glob/arb.2',
                                './tests/testfiles/glob/arb.2.2',
                                './tests/testfiles/glob/sub/arbsub.2',
                                './tests/testfiles/glob/arb.3',
                                './tests/testfiles/glob/sub/arbsub.3'])


def test_get_glob_wrong_type():
    """Wrong type raises."""
    with pytest.raises(TypeError) as err:
        filesystem.get_glob(1)

    assert str(err.value) == ("path should be string, path-like or a list. "
                              "Instead, it's a <class 'int'>")


def test_get_glob_path_doesnt_exist():
    """Non existent paths return nothing."""
    paths = filesystem.get_glob(['./arbX', './arb/**/x'])
    assert not paths
# endregion get_glob

# region is_same_file


def test_is_same_file():
    """Same file is same."""
    assert filesystem.is_same_file('./tests/testfiles/test.txt',
                                   './tests/testfiles/test.txt')


def test_is_same_file_path():
    """Same file is same with path input."""
    assert filesystem.is_same_file(Path('./tests/testfiles/test.txt'),
                                   Path('./tests/testfiles/test.txt'))


def test_is_same_file_relative_paths_resolve():
    """Same file with relative path obfuscation."""
    assert filesystem.is_same_file(
        './tests/testfiles/test.txt',
        './tests/testfiles/../../tests/testfiles/test.txt')


def test_is_same_file_dirs():
    """Directories aren't files."""
    assert not filesystem.is_same_file('./tests', './../tests/')


def test_is_same_file_one_exists_other_doesnt():
    """One file exists, the other doesn't."""
    assert not filesystem.is_same_file('./tests/testfiles/test.txt', './arb')


def test_is_same_file_paths_dont_exist():
    """Nonsense paths not same."""
    assert not filesystem.is_same_file('arb/arb', 'arb/arb')
    assert not filesystem.is_same_file('arb/arb1', 'arb/arb')
    assert not filesystem.is_same_file('arb/arb2', None)
    assert not filesystem.is_same_file(None, None)
# endregion is_same_file

# region move_file


def test_move_file_new(temp_dir, temp_file_creator):
    """Move file moves file if destination doesn't exist."""
    file1 = temp_file_creator()
    with open(file1, 'w') as f1:
        f1.write('arb file content')

    file2 = temp_dir.joinpath('file2')

    filesystem.move_file(file1, file2)
    assert not file1.is_file()
    assert file2.is_file()

    with open(file2) as f2:
        assert f2.read() == 'arb file content'


def test_move_file_new_str(temp_dir, temp_file_creator):
    """Move file moves file if destination doesn't exist, input str."""
    file1 = temp_file_creator()
    with open(file1, 'w') as f1:
        f1.write('arb file content')

    file2 = temp_dir.joinpath('file2')

    filesystem.move_file(str(file1), str(file2))
    assert not file1.is_file()
    assert file2.is_file()

    with open(file2) as f2:
        assert f2.read() == 'arb file content'


def test_move_file_overwrite(temp_file_creator):
    """Move file overwrites existing file."""
    file1 = temp_file_creator()
    with open(file1, 'w') as f1:
        f1.write('arb file content')

    file2 = temp_file_creator()

    filesystem.move_file(file1, file2)
    assert not file1.is_file()
    assert file2.is_file()

    with open(file2) as f2:
        assert f2.read() == 'arb file content'


def test_move_file_dest_parent_not_exist(temp_dir, temp_file_creator):
    """Move file fails if destination parent doesn't exist."""
    file1 = temp_file_creator()

    file2 = temp_dir.joinpath('blah', 'file2')

    with pytest.raises(FileNotFoundError) as err:
        filesystem.move_file(file1, file2)

    the_err = err.value
    assert file1 == Path(the_err.filename)
    assert file2 == Path(the_err.filename2)

    assert file1.is_file()
    assert not file2.is_file()
# endregion move_file

# region move_temp_file


def test_move_temp_file_new(temp_dir, temp_file_creator):
    """Move temp file moves file if destination doesn't exist."""
    file1 = temp_file_creator()
    with open(file1, 'w') as f1:
        f1.write('arb file content')

    file2 = temp_dir.joinpath('file2')

    filesystem.move_temp_file(file1, file2)
    assert not file1.is_file()
    assert file2.is_file()

    with open(file2) as f2:
        assert f2.read() == 'arb file content'


def test_move_temp_file_dest_parent_not_exist(temp_dir, temp_file_creator):
    """Move temp file fails if destination parent doesn't exist, wipes src."""
    file1 = temp_file_creator()

    file2 = temp_dir.joinpath('blah', 'file2')

    with pytest.raises(FileNotFoundError) as err:
        filesystem.move_temp_file(file1, file2)

    the_err = err.value
    assert file1 == Path(the_err.filename)
    assert file2 == Path(the_err.filename2)

    assert not file1.is_file()
    assert not file2.is_file()


@patch('os.remove', side_effect=ValueError('test remove failed'))
def test_move_temp_file_err_removing_src(mock_remove,
                                         temp_dir,
                                         temp_file_creator):
    """Move temp file fails if can't remove src on clean-up."""
    file1 = temp_file_creator()

    file2 = temp_dir.joinpath('blah', 'file2')

    with patch_logger(
            'pypyr.utils.filesystem', logging.ERROR
    ) as mock_logger_err:
        with pytest.raises(FileNotFoundError) as err:
            filesystem.move_temp_file(file1, file2)

    the_err = err.value
    assert file1 == Path(the_err.filename)
    assert file2 == Path(the_err.filename2)

    assert mock_logger_err.mock_calls == [
        call(f"error moving file {file1} to {file2}. {the_err}"),
        call(f'error removing temp file {file1}. test remove failed')]

    assert file1.is_file()
    assert not file2.is_file()


def test_move_temp_file_new_relative_paths(temp_dir, temp_file_creator):
    """Move temp file moves file if destination doesn't exist."""
    file1 = temp_file_creator()
    with open(file1, 'w') as f1:
        f1.write('arb file content')

    file2 = temp_dir.joinpath('file2')

    # work out relative paths to cwd
    rel_path1 = os.path.relpath(file1)
    rel_path2 = os.path.relpath(file2)

    filesystem.move_temp_file(rel_path1, rel_path2)
    assert not file1.is_file()
    assert file2.is_file()

    with open(file2) as f2:
        assert f2.read() == 'arb file content'

# endregion move__temp_file
