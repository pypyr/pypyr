"""pypyr step yaml definition classes - domain specific language."""
from functools import reduce
import logging

from pypyr.config import config
from pypyr.utils.asserts import assert_key_has_value
from pypyr.utils.filesystem import (ObjectRewriter,
                                    StreamRewriter)


logger = logging.getLogger(__name__)


class FileInRewriterStep():
    """A pypyr step that represents a file in-out rewriter.

    This models a step that takes config like this:
        root_key:
            in: str/path-like, or list of str/paths. Mandatory.
            out: str/path-like. Optional.
            encoding: str. Optional. Encoding to use on both in & out.
            encodingIn: str. Optional. Encoding to use on reading In.
            encodingOut: str. Optional. Encoding to use on reading Out.

    If you do not set encoding, will use the system default, which is utf-8
    for everything except windows.

    Set 'encoding' to override system default for both in & out. Use encodingIn
    and encodingOut instead when you want different encodings for reading in
    and writing out.

    The run_step method does the actual work.
    """

    def __init__(self, name, root_key, context):
        """Initialize the FileInRewriterStep.

        The step config in the context dict looks like this:
            root_key:
                in: str/path-like, or list of str/paths. Mandatory.
                out: str/path-like. Optional.
                encoding: str. Optional. Encoding to use on both in & out.
                encodingIn: str. Optional. Encoding to use on reading In.
                encodingOut: str. Optional. Encoding to use on writing Out.
        Args:
            name: Unique name for step. Likely __name__ of calling step.
            root_key: str. Context key name where step's config is saved under.
            context: pypyr.context.Context. Look for config in this context
                     instance.

        """
        assert name, ("name parameter must exist for FileInRewriterStep.")
        assert root_key, ("root_key param must exist for FileInRewriterStep.")
        assert context, ("context param must exist for FileInRewriterStep.")
        # this way, logs output as the calling step, which makes more sense
        # to end-user than a mystery steps.dsl.blah logging output.
        self.logger = logging.getLogger(name)

        self.context = context
        context.assert_key_has_value(root_key, name)
        root_dict = context.get_formatted(root_key)
        self.formatted_root = root_dict

        assert_key_has_value(obj=root_dict,
                             key='in',
                             caller=name,
                             parent=root_key)

        self.path_in = root_dict['in']
        self.path_out = root_dict.get('out', None)

        encoding = root_dict.get('encoding', config.default_encoding)

        self.encoding_in = root_dict.get('encodingIn', encoding)
        self.encoding_out = root_dict.get('encodingOut', encoding)

    def run_step(self, rewriter):
        """Do the file in to out rewrite.

        Doesn't do anything more crazy than call files_in_to_out on the
        rewriter.

        Args:
            rewriter: pypyr.filesystem.FileRewriter instance.
        """
        assert rewriter, ("FileRewriter instance required to run "
                          "FileInRewriterStep.")
        rewriter.files_in_to_out(in_path=self.path_in, out_path=self.path_out)


class ObjectRewriterStep(FileInRewriterStep):
    """A pypyr step that uses an object representer to rewrite files in out."""

    def run_step(self, representer):
        """Do the object in-out rewrite.

        Args:
            representer: A pypyr.filesystem.ObjectRepresenter instance.

        """
        assert representer, ("ObjectRepresenter instance required to run "
                             "ObjectRewriterStep.")
        rewriter = ObjectRewriter(self.context.get_formatted_value,
                                  representer,
                                  encoding_in=self.encoding_in,
                                  encoding_out=self.encoding_out)
        super().run_step(rewriter)


class StreamRewriterStep(FileInRewriterStep):
    """A pypyr step that uses a streaming file in-out rewriter.

    This models a step that takes config like this:
        root_key:
            in: str/path-like, or list of str/paths. Mandatory.
            out: str/path-like. Optional.
            replacePairs: mandatory. Dictionary where items are:
                          'find_string': 'replace_string'

    """

    def run_step(self):
        """Do the file in-out rewrite."""
        rewriter = StreamRewriter(self.context.iter_formatted_strings,
                                  encoding_in=self.encoding_in,
                                  encoding_out=self.encoding_out)
        super().run_step(rewriter)


class StreamReplacePairsRewriterStep(FileInRewriterStep):
    """A stream rewriter step that uses replacePairs."""

    def __init__(self, name, root_key, context):
        """Initialize the FileInRewriterStep.

        The step config in the context dict looks like this:
            root_key:
                in: str/path-like, or list of str/paths. Mandatory.
                out: str/path-like. Optional.
                replacePairs: mandatory. Dictionary where items are:
                    'find_string': 'replace_string'
                encoding: str. Optional. Encoding to use on both in & out.
                encodingIn: str. Optional. Encoding to use on reading In.
                encodingOut: str. Optional. Encoding to use on writing Out.

        If you do not set encoding, will use the system default, which is utf-8
        for everything except windows.

        Set 'encoding' to override system default for both in & out. Use
        encodingIn and encodingOut instead when you want different encodings
        for reading in and writing out.

        Args:
            name: Unique name for step. Likely __name__ of calling step.
            root_key: str. Context key name where step's config is saved under.
            context: pypyr.context.Context. Look for config in this context
                     instance.

        Returns: None
        """
        super().__init__(name=name, root_key=root_key, context=context)
        root_dict = self.formatted_root

        assert_key_has_value(obj=root_dict,
                             key='replacePairs',
                             caller=name,
                             parent=root_key)

        self.replace_pairs = root_dict['replacePairs']

    def run_step(self):
        """Write in to out, replacing strings per the replace_pairs."""
        formatted_replacements = self.context.get_formatted_value(
            self.replace_pairs)

        iter = StreamReplacePairsRewriterStep.iter_replace_strings(
            formatted_replacements)
        rewriter = StreamRewriter(iter,
                                  encoding_in=self.encoding_in,
                                  encoding_out=self.encoding_out)
        super().run_step(rewriter)

    @staticmethod
    def iter_replace_strings(replacements):
        """Create a function that uses replacement pairs to process a string.

        The returned function takes an iterator and yields on each processed
        line.

        Args:
            replacements: Dict containing 'find_string': 'replace_string' pairs

        Returns:
            function with signature: iterator of strings = function(iterable)

        """
        def function_iter_replace_strings(iterable_strings):
            """Yield a formatted string from iterable_strings using a generator.

            Args:
                iterable_strings: Iterable containing strings. E.g a file-like
                                  object.

            Returns:
                Yields formatted line.

            """
            for string in iterable_strings:
                yield reduce((lambda s, kv: s.replace(*kv)),
                             replacements.items(),
                             string)

        return function_iter_replace_strings
