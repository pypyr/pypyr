"""pypyr step yaml definition classes - domain specific language."""
from functools import reduce
import logging
from pypyr.utils.filesystem import (ObjectRewriter,
                                    StreamRewriter)

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


class FileInRewriterStep():
    """A pypyr step that represents a file in-out rewriter.

    This models a step that takes config like this:
        root_key:
            in: str/path-like, or list of str/paths. Mandatory.
            out: str/path-like. Optional.

    The run_step method does the actual work.
    """

    def __init__(self, name, root_key, context):
        """Initialize the FileInRewriterStep.

        The step config in the context dict looks like this:
            root_key:
                in: str/path-like, or list of str/paths. Mandatory.
                out: str/path-like. Optional.
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
        root_dict = context[root_key]
        # this verifies both root_key and child exists
        context.assert_child_key_has_value(parent=root_key,
                                           child='in',
                                           caller=name)

        self.path_in = context.get_formatted_iterable(root_dict['in'])
        out = root_dict.get('out', None)
        if out:
            self.path_out = context.get_formatted_string(out)
        else:
            self.path_out = None

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
        rewriter = ObjectRewriter(self.context.get_formatted_iterable,
                                  representer)
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
        rewriter = StreamRewriter(self.context.iter_formatted_strings)
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
        Args:
            name: Unique name for step. Likely __name__ of calling step.
            root_key: str. Context key name where step's config is saved under.
            context: pypyr.context.Context. Look for config in this context
                     instance.

        """
        super().__init__(name=name, root_key=root_key, context=context)
        # this verifies both root_key and child exists
        context.assert_child_key_has_value(parent=root_key,
                                           child='replacePairs',
                                           caller=name)

        self.replace_pairs = context[root_key]['replacePairs']

    def run_step(self):
        """Write in to out, replacing strings per the replace_pairs."""
        formatted_replacements = self.context.get_formatted_iterable(
            self.replace_pairs)

        iter = StreamReplacePairsRewriterStep.iter_replace_strings(
            formatted_replacements)
        rewriter = StreamRewriter(iter)
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
