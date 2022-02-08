"""Utility functions for file system operations. Read, format files, write."""
from abc import ABC, abstractmethod
import glob
from itertools import chain
import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from pypyr.config import config
from pypyr.errors import Error
import pypyr.toml
import pypyr.yaml

logger = logging.getLogger(__name__)

# region Rewriters


class FileRewriter(ABC):
    """FileRewriter reads input file, formats it and write to output file.

    Use this abstract base class to implement rewriters.

    This base class contains useful functionality to loop through input and
    output paths, leaving the handling of individual files up to the deriving
    classes.
    """

    def __init__(self, formatter, encoding_in=None, encoding_out=None):
        """Initialize formatter.

        Args:
            formatter: Callable object that will format the IN file payload to
                       create OUT file.
            encoding_in: str | None. Encoding when reading input.
            encoding_out: str | None. Encoding when reading output.

        If you do not set encoding, will use the system default, which is utf-8
        for everything except windows.

        """
        self.formatter = formatter
        self.encoding_in = encoding_in
        self.encoding_out = encoding_out

    @abstractmethod
    def in_to_out(self, in_path, out_path):
        """Take in_path, applies formatting, writes to out_path.

        Input arguments can be str or path-like. Relative or absolute paths
        will work.

        Args:
            in_path: str or path-like. Must refer to a single existing file.
            out_path: str or path-like. Must refer to a single destination file
                      location. will create directory structure if it doesn't
                      exist.
        Returns:
            None.

        """
        raise NotImplementedError(
            'you must implement in_to_out(in_path, out_path) for a '
            'FileFormatter')

    def files_in_to_out(self, in_path, out_path=None):
        """Write in files to out, calling the line_handler on each line.

        Calls file_in_to_out under the hood to format the in_path payload. The
        formatting processing is done by the self.formatter instance.

        Args:
            in_path: str, path-like, or an iterable (list/tuple) of
                     strings/paths. Each str/path can be a glob, relative or
                     absolute path.
            out_path: str or path-like. Can refer to a file or a directory.
                      will create directory structure if it doesn't exist. If
                      in-path refers to >1 file (e.g it's a glob or list), out
                      path can only be a directory - it doesn't make sense to
                      write >1 file to the same single file (this is no an
                      appender.) To ensure out_path is read as a directory and
                      not a file, be sure to have the path separator (/) at the
                      end.
                      Top tip: Path-like objects strip the trailing slash. If
                      you want to pass in a dir that does not exist yet as
                      out-path with a trailing /, you should be passing it as a
                      str to preserve the /.
                      If out_path is not specified or None, will in-place edit
                      and overwrite the in-files.

        Returns:
            None.

        """
        in_paths = get_glob(in_path)

        in_count = len(in_paths)
        if in_count == 0:
            logger.debug(f'in path found {in_count} paths.')
        else:
            logger.debug(f'in path found {in_count} paths:')
            for path in in_paths:
                logger.debug(f'{path}')
            logger.debug(
                'herewith ends the paths. will now process each file.')

        if in_paths:
            # derive the destination directory, ensure it's ready for writing
            basedir_out = None
            is_outfile_name_known = False
            if out_path:
                # outpath could be a file, or a dir
                pathlib_out = Path(out_path)
                # yep, Path() strips trailing /, hence check original string
                if FileRewriter.is_str_dir(out_path):
                    # ensure dir - mimic posix mkdir -p
                    pathlib_out.mkdir(parents=True, exist_ok=True)
                    basedir_out = pathlib_out
                elif pathlib_out.is_dir():
                    basedir_out = pathlib_out
                else:
                    if len(in_paths) > 1:
                        raise Error(
                            f'{in_path} resolves to {len(in_paths)} files, '
                            'but you specified only a single file as out '
                            f'{out_path}. If the outpath is meant to be a '
                            'directory, put a / at the end.')

                    # at this point it must be a file (not dir) path
                    # make sure that the parent dir exists
                    basedir_out = pathlib_out.parent
                    basedir_out.mkdir(parents=True, exist_ok=True)
                    is_outfile_name_known = True

            # loop through all the in files and write them to the out dir
            file_counter = 0
            is_edit = False
            for path in in_paths:
                actual_in = Path(path)
                # recursive glob returns dirs too, only interested in files
                if actual_in.is_file():
                    if basedir_out:
                        if is_outfile_name_known:
                            actual_out = pathlib_out
                        else:
                            # default to original src file name if only out dir
                            # specified without an out file name
                            actual_out = basedir_out.joinpath(actual_in.name)

                        logger.debug("writing %s to %s", path, actual_out)
                        self.in_to_out(in_path=actual_in, out_path=actual_out)
                    else:
                        logger.debug("editing %s", path)
                        self.in_to_out(in_path=actual_in)
                        is_edit = True
                    file_counter += 1

            if is_edit:
                logger.info(
                    "edited & wrote %s file(s) at %s", file_counter, in_path)
            else:
                logger.info(
                    "read %s, formatted and wrote %s file(s) to %s",
                    in_path, file_counter, out_path)
        else:
            logger.info("%s found no files", in_path)

    @staticmethod
    def is_str_dir(s: str) -> bool:
        """Return True if s ends with platform's dir separator(s)."""
        if isinstance(s, str):
            if config.is_windows:
                # Not using os.sep here, because on windows pythonistas will
                # use / as separator as easily as \.
                # this is fine because win won't allow either / or \
                # in filenames.
                if s[-1] in {'/', '\\'}:
                    return True
            else:
                # on posix only check for /.
                if s.endswith(os.sep):
                    return True
        return False


class ObjectRewriter(FileRewriter):
    """Load a single file into an object, run formatter on it and write out.

    Object instantiation takes a formatter.
    writer = StreamRewriter(formatter)

    Formatter signature: iterable = formatter(iterable)
    It returns an iterator. The single input argument is an iterable.
    Tip, use function or callable object with __call__

    Object instantion also takes an ObjectRepresenter. An ObjectRepresenter
    has a load and a dump method that handles the object deserialization and
    serialization.
    """

    def __init__(self, formatter, object_representer,
                 encoding_in=None, encoding_out=None):
        """Initialize formatter and object representer.

        Args:
            formatter: Callable object/function that will format object loaded
                       from in file. Formatter signature:
                       iterable = formatter(iterable)
            object_representer: An ObjectRepresenter instance.
            encoding_in: str | None. Optional. Encoding when reading input.
            encoding_out: str | None. Optional. Encoding when reading output.

        If you do not set encoding, will use the system default, which is utf-8
        for everything except windows.
        """
        super().__init__(formatter, encoding_in, encoding_out)
        self.object_representer = object_representer

    def in_to_out(self, in_path, out_path=None):
        """Load file into object, formats, writes object to out.

        If in_path and out_path point to the same thing it will in-place edit
        and overwrite the in path. Even easier, if you do want to edit a file
        in place, don't specify out_path, or set it to None.

        Args:
            in_path: str or path-like. Must refer to a single existing file.
            out_path: str or path-like. Must refer to a single destination file
                      location. will create directory structure if it doesn't
                      exist.
                      If out_path is not specified or None, will in-place edit
                      and overwrite the in-files.

        Returns:
            None.

        """
        if is_same_file(in_path, out_path):
            logger.debug(
                "in path and out path are the same file. writing to temp "
                "file and then replacing in path with the temp file.")
            out_path = None

        logger.debug("opening source file: %s", in_path)

        read_mode = self.object_representer.read_mode

        with open(in_path, read_mode, encoding=self.encoding_in) as infile:
            obj = self.object_representer.load(infile)

        write_mode = self.object_representer.write_mode
        if out_path:
            logger.debug(
                f"opening destination file for writing: {out_path}")
            # out directory must exist
            with open(out_path, write_mode,
                      encoding=self.encoding_out) as outfile:
                self.object_representer.dump(outfile, self.formatter(obj))
            return
        else:
            logger.debug("opening temp file for writing...")
            with NamedTemporaryFile(mode=write_mode,
                                    dir=os.path.dirname(in_path),
                                    delete=False,
                                    encoding=self.encoding_out) as outfile:
                self.object_representer.dump(outfile, self.formatter(obj))

            logger.debug("moving temp file to: %s", in_path)

            move_temp_file(outfile.name, infile.name)


class StreamRewriter(FileRewriter):
    """Streaming style in-to-out reader and writer.

    Reads IN file  line-by-line, formats each line and writes to OUT in a
    stream. You can expect memory use to stay more or less flat, depending on
    how big your lines are.

    Object instantiation takes a formatter.
    writer = StreamRewriter(formatter)

    Formatter signature: iterator = formatter(iterable)
    It returns an iterator. The single input argument is an iterable.
    Tip, use function or callable object with __call__

    """

    def in_to_out(self, in_path, out_path=None):
        """Write a single file in to out, running self.formatter on each line.

        If in_path and out_path point to the same thing it will in-place edit
        and overwrite the in path. Even easier, if you do want to edit a file
        in place, don't specify out_path, or set it to None.

        Args:
            in_path: str or path-like. Must refer to a single existing file.
            out_path: str or path-like. Must refer to a single destination file
                      location. will create directory structure if it doesn't
                      exist.
                      If out_path is not specified or None, will in-place edit
                      and overwrite the in-files.

        Returns:
            None.

        """
        is_in_place_edit = False
        if is_same_file(in_path, out_path):
            logger.debug(
                "in path and out path are the same file. writing to temp "
                "file and then replacing in path with the temp file.")
            out_path = None
            is_in_place_edit = True

        logger.debug("opening source file: %s", in_path)
        with open(in_path, encoding=self.encoding_in) as infile:
            if out_path:
                logger.debug(
                    "opening destination file for writing: %s", out_path)
                # at this point out dir must exist
                with open(out_path, 'w',
                          encoding=self.encoding_out) as outfile:
                    outfile.writelines(self.formatter(infile))
                return
            else:
                logger.debug("opening temp file for writing...")
                with NamedTemporaryFile(mode='w+t',
                                        dir=os.path.dirname(in_path),
                                        delete=False,
                                        encoding=self.encoding_out) as outfile:
                    outfile.writelines(self.formatter(infile))

                is_in_place_edit = True

        # only replace infile AFTER it's closed, outside the with.
        # pragma exclude because func actually returns on 287 in if out_path,
        # and cov not smart enough to realize that !is_in_place_edit won't ever
        # happen here (the function will have exited already)
        if is_in_place_edit:    # pragma: no branch
            logger.debug("moving temp file to: %s", in_path)
            move_temp_file(outfile.name, infile.name)

# endregion Rewriters

# region Representers


class ObjectRepresenter(ABC):
    """Abstract base class to handle object serialization and deserialization.

    Derive from this base class to create your own object representers that can
    serialize and deserialize a payload.

    This tends to be useful for the ObjectRewriter.

    Attributes:
        read_mode: open underlying file in text 'rt' or binary 'rb' mode.
        write_mode: open underlying file in text 'wt' or binary 'wb' mode.
    """

    def __init__(self, is_binary=False):
        """Initialize object representer in binary or text mode.

        Args:
            is_binary (bool): Set true if representer expects bytes, not str.
        """
        if is_binary:
            self.read_mode = 'rb'
            self.write_mode = 'wb'
        else:
            self.read_mode = 'rt'
            self.write_mode = 'wt'

    @abstractmethod
    def load(self, file):
        """Instantiate object from input file."""
        pass

    @abstractmethod
    def dump(self, file, payload):
        """Serialize payload to file."""
        pass


class JsonRepresenter(ObjectRepresenter):
    """Load and dump a json payload. Useful for ObjectRewriter."""

    def load(self, file):
        """Load Json object from open file input.

        Args:
            file: Open file-like object.

        Returns:
            Json represented as a python object.
        """
        return json.load(file)

    def dump(self, file, payload):
        """Dump json object to open file output.

        Writes json with 2 spaces indentation.

        Args:
            file: Open file-like object. Must be open for writing.
            payload: The Json object to write to file.

        Returns:
            None.

        """
        json.dump(payload, file, indent=config.json_indent,
                  ensure_ascii=config.json_ascii)


class TomlRepresenter(ObjectRepresenter):
    """Load and dump a toml payload. Useful for ObjectRewriter."""

    def __init__(self):
        """Initialize in binary mode."""
        super().__init__(True)

    def load(self, file):
        """Load Toml object from open file input.

        Args:
            file: Open file-like object in binary mode.

        Returns:
            Dict.
        """
        return pypyr.toml.load(file)

    def dump(self, file, payload):
        """Dump toml object to open file output.

        Args:
            file: Open file-like object. Must be open for binary writing.
            payload: The Toml object to write to file.

        Returns:
            None.
        """
        pypyr.toml.dump(payload, file)


class YamlRepresenter(ObjectRepresenter):
    """Load and dump a Yaml payload. Useful for ObjectRewriter."""

    def __init__(self):
        """Instantiate the yaml representer."""
        super().__init__()
        self.yaml_parser = pypyr.yaml.get_yaml_parser_roundtrip()

    def load(self, file):
        """Load Yaml object from open file input.

        This uses a safe loader, so only recognized yaml types allowed.

        Args:
            file: Open file-like object.

        Returns:
            Yaml represented as python object.
        """
        return self.yaml_parser.load(file)

    def dump(self, file, payload):
        """Dump yaml oject to open file output.

        Writes yaml with 2 spaces indentation.

        Args:
            file: Open file-like object. Must be open for writing.
            payload: The yaml object to write to file.

        Returns:
            None.

        """
        self.yaml_parser.dump(payload, file)

# endregion Representers


def ensure_dir(path):
    """Create all parent directories of path if they don't exist.

    Args:
        path. Path-like object. Create parent dirs to this path.

    Return:
        None.

    """
    os.makedirs(os.path.abspath(os.path.dirname(path)), exist_ok=True)


def get_glob(path):
    """Process the input path, applying globbing and formatting.

    Do note that this will returns files AND directories that match the glob.

    No tilde expansion is done, but *, ?, and character ranges expressed with
    [] will be correctly matched.

    Escape all special characters ('?', '*' and '['). For a literal match, wrap
    the meta-characters in brackets. For example, '[?]' matches the character
    '?'.

    If passing in an iterable of paths, will expand matches for each path in
    the iterable. The function will return all the matches for each path
    glob expression combined into a single list.

    Args:
        path: Path-like string, or iterable (list or tuple ) of paths.

    Returns:
        Combined list of paths found for input glob.

    """
    if isinstance(path, str):
        return glob.glob(path, recursive=True)
    if isinstance(path, os.PathLike):
        # hilariously enough, glob doesn't like path-like. Gotta be str.
        return glob.glob(str(path), recursive=True)
    elif isinstance(path, (list, tuple)):
        # each glob returns a list, so chain all the lists into one big list
        return list(chain.from_iterable(
            glob.glob(str(p), recursive=True) for p in path))
    else:
        raise TypeError("path should be string, path-like or a list. Instead, "
                        f"it's a {type(path)}")


def is_same_file(path1, path2):
    """Return True if path1 is the same file as path2.

    The reason for this dance is that samefile throws if either file doesn't
    exist.

    Args:
        path1: str or path-like.
        path2: str or path-like.

    Returns:
        bool. True if the same file, False if not.

    """
    return (
        path1 and path2
        and os.path.isfile(path1) and os.path.isfile(path2)
        and os.path.samefile(path1, path2))


def move_file(src, dest):
    """Move source file to destination.

    Overwrites dest.

    Args:
        src: str or path-like. source file
        dest: str or path-like. destination file

    Returns:
        None.

    Raises:
        FileNotFoundError: out path parent doesn't exist.
        OSError: if any IO operations go wrong.

    """
    try:
        os.replace(src, dest)
    except Exception as ex_replace:
        logger.error("error moving file %s to "
                     "%s. %s", src, dest, ex_replace)
        raise


def move_temp_file(src, dest):
    """Move src to dest. Delete src if something goes wrong.

    Overwrites dest.

    Args:
        src: str or path-like. source file
        dest: str or path-like. destination file

    Returns:
        None.

    Raises:
        FileNotFoundError: out path parent doesn't exist.
        OSError: if any IO operations go wrong. Does its best to clean up after
                 itself and remove temp files.

    """
    try:
        move_file(src, dest)
    except Exception:
        try:
            os.remove(src)
        except Exception as ex_clean:
            # at this point, something's deeply wrong, so log error.
            # raising the original error, though, not this error in the
            # error handler, as the 1st was the initial cause of all of
            # this.
            logger.error("error removing temp file %s. %s",
                         src, ex_clean)

        raise
