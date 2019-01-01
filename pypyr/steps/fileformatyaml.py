"""pypyr step that parses yaml for string substitutions, writes output."""
import logging
from pypyr.steps.dsl.fileinoutrewriter import ObjectRewriterStep
from pypyr.utils.filesystem import YamlRepresenter

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Parse input yaml file and substitute {tokens} from context.

    Loads yaml into memory to do parsing, so be aware of big files.

    Args:
        context: pypyr.context.Context. Mandatory.
        - fileFormatYaml
            - in. mandatory.
              str, path-like, or an iterable (list/tuple) of
              strings/paths. Each str/path can be a glob, relative or
              absolute path.
            - out. optional. path-like.
              Can refer to a file or a directory.
              will create directory structure if it doesn't exist. If
              in-path refers to >1 file (e.g it's a glob or list), out
              path can only be a directory - it doesn't make sense to
              write >1 file to the same single file (this is not an
              appender.) To ensure out_path is read as a directory and
              not a file, be sure to have the path separator (/) at the
              end.
              If out_path is not specified or None, will in-place edit
              and overwrite the in-files.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormatYaml or
            fileFormatYaml['in'] missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileFormatYaml or
            fileFormatYaml['in'] exists but is None.

    """
    logger.debug("started")

    deprecated(context)

    ObjectRewriterStep(__name__, 'fileFormatYaml', context).run_step(
        YamlRepresenter())

    logger.debug("done")


def deprecated(context):
    """Create new style in params from deprecated."""
    if 'fileFormatYamlIn' in context:
        context.assert_keys_have_values(__name__,
                                        'fileFormatYamlIn',
                                        'fileFormatYamlOut')

        context['fileFormatYaml'] = {'in': context['fileFormatYamlIn'],
                                     'out': context['fileFormatYamlOut']}

        logger.warning("fileFormatYamlIn and fileFormatYamlOut "
                       "are deprecated. They will stop working upon the next "
                       "major release. Use the new context key fileFormatYaml "
                       "instead. It's a lot better, promise! For the moment "
                       "pypyr is creating the new fileFormatYaml key for you "
                       "under the hood.")
