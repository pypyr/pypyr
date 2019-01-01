"""Archive and extract tars."""
import logging
import tarfile
from pypyr.errors import KeyNotInContextError

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Archive and/or extract tars with or without compression.

    Args:
        context: dictionary-like. Mandatory.

        Expects the following context:
        tar:
            extract:
                - in: /path/my.tar
                  out: /out/path
            archive:
                - in: /dir/to/archive
                  out: /out/destination.tar
            format: ''

        tar['format'] - if not specified, defaults to lzma/xz
                       Available options:
                        - '' - no compression
                        - gz (gzip)
                        - bz2 (bzip2)
                        - xz (lzma)

    This step will run whatever combination of Extract and Archive you specify.
    Regardless of combination, execution order is Extract, Archive.

    Source and destination paths support {key} string interpolation.

    Never extract archives from untrusted sources without prior inspection.
    It is possible that files are created outside of path, e.g. members that
    have absolute filenames starting with "/" or filenames with two dots "..".
    """
    logger.debug("started")

    assert context, f"context must have value for {__name__}"

    deprecated(context)
    found_at_least_one = False

    context.assert_key_has_value('tar', __name__)

    tar = context['tar']
    if 'extract' in tar:
        found_at_least_one = True
        tar_extract(context)

    if 'archive' in tar:
        found_at_least_one = True
        tar_archive(context)

    if not found_at_least_one:
        # This will raise exception on first item with a problem.
        raise KeyNotInContextError('pypyr.steps.tar must have either extract '
                                   'or archive specified under the tar key. '
                                   'Or both of these. It has neither.')

    logger.debug("done")


def get_file_mode_for_reading(context):
    """Get file mode for reading from tar['format'].

    This should return r:*, r:gz, r:bz2 or r:xz. If user specified something
    wacky in tar.Format, that's their business.

    In theory r:* will auto-deduce the correct format.
    """
    format = context['tar'].get('format', None)

    if format or format == '':
        mode = f"r:{context.get_formatted_string(format)}"
    else:
        mode = 'r:*'

    return mode


def get_file_mode_for_writing(context):
    """Get file mode for writing from tar['format'].

    This should return w:, w:gz, w:bz2 or w:xz. If user specified something
    wacky in tar.Format, that's their business.
    """
    format = context['tar'].get('format', None)
    # slightly weird double-check because falsy format could mean either format
    # doesn't exist in input, OR that it exists and is empty. Exists-but-empty
    # has special meaning - default to no compression.
    if format or format == '':
        mode = f"w:{context.get_formatted_string(format)}"
    else:
        mode = 'w:xz'

    return mode


def tar_archive(context):
    """Archive specified path to a tar archive.

    Args:
        context: dictionary-like. context is mandatory.
            context['tar']['archive'] must exist. It's a dictionary.
            keys are the paths to archive.
            values are the destination output paths.

    Example:
        tar:
            archive:
                - in: path/to/dir
                  out: path/to/destination.tar.xs
                - in: another/my.file
                  out: ./my.tar.xs

        This will archive directory path/to/dir to path/to/destination.tar.xs,
        and also archive file another/my.file to ./my.tar.xs
    """
    logger.debug("start")

    mode = get_file_mode_for_writing(context)

    for item in context['tar']['archive']:
        # value is the destination tar. Allow string interpolation.
        destination = context.get_formatted_string(item['out'])
        # key is the source to archive
        source = context.get_formatted_string(item['in'])
        with tarfile.open(destination, mode) as archive_me:
            logger.debug(f"Archiving '{source}' to '{destination}'")

            archive_me.add(source, arcname='.')
            logger.info(f"Archived '{source}' to '{destination}'")

    logger.debug("end")


def tar_extract(context):
    """Extract all members of tar archive to specified path.

    Args:
        context: dictionary-like. context is mandatory.
            context['tar']['extract'] must exist. It's a dictionary.
            keys are the path to the tar to extract.
            values are the destination paths.

    Example:
        tar:
            extract:
                - in: path/to/my.tar.xs
                  out: /path/extract/here
                - in: another/tar.xs
                  out: .

        This will extract path/to/my.tar.xs to /path/extract/here, and also
        extract another/tar.xs to $PWD.
    """
    logger.debug("start")

    mode = get_file_mode_for_reading(context)

    for item in context['tar']['extract']:
        # in is the path to the tar to extract. Allows string interpolation.
        source = context.get_formatted_string(item['in'])
        # out is the outdir, dhur. Allows string interpolation.
        destination = context.get_formatted_string(item['out'])
        with tarfile.open(source, mode) as extract_me:
            logger.debug(f"Extracting '{source}' to '{destination}'")

            extract_me.extractall(destination)
            logger.info(f"Extracted '{source}' to '{destination}'")

    logger.debug("end")


def deprecated(context):
    """Handle deprecated context input."""
    tar = context.get('tar', None)

    # at least 1 of tarExtract or tarArchive must exist in context
    tar_extract, tar_archive = context.keys_of_type_exist(
        ('tarExtract', list),
        ('tarArchive', list))

    found_at_least_one = (tar_extract.key_in_context
                          or tar_archive.key_in_context)

    if tar and not found_at_least_one:
        return
    elif found_at_least_one:
        tar = context['tar'] = {}

    if tar_extract.key_in_context and tar_extract.is_expected_type:
        tar['extract'] = context[tar_extract.key]

    if tar_archive.key_in_context and tar_archive.is_expected_type:
        tar['archive'] = context[tar_archive.key]

    if 'tarFormat' in context:
        tar['format'] = context['tarFormat']

    logger.warning("tarExtract and tarArchive are deprecated. They will "
                   "stop working upon the next major release. "
                   "Use the new context key env instead. It's a lot "
                   "better, promise! For the moment pypyr is creating the "
                   "new env key for you under the hood.")
