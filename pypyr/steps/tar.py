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

        At least one of these context keys must exist:
        context['tarExtract']
        context['tarArchive']

        Optional:
        context['tarFormat'] - if not specified, defaults to lzma/xz
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

    # at least 1 of tarExtract or tarArchive must exist in context
    tarExtract, tarArchive = context.keys_of_type_exist(
        ('tarExtract', list),
        ('tarArchive', list)
    )
    found_at_least_one = False

    if tarExtract.key_in_context and tarExtract.is_expected_type:
        found_at_least_one = True
        tar_extract(context)

    if tarArchive.key_in_context and tarArchive.is_expected_type:
        found_at_least_one = True
        tar_archive(context)

    if not found_at_least_one:
        # This will raise exception on first item with a problem.
        context.assert_keys_type_value(__name__,
                                       ('This step needs any combination of '
                                        'tarExtract or tarArchive in context.'
                                        ),
                                       tarExtract,
                                       tarArchive)

    logger.debug("done")


def get_file_mode_for_reading(context):
    """Get file mode for reading from context['tarFormat'].

    This should return r:*, r:gz, r:bz2 or r:xz. If user specified something
    wacky in tarFormat, that's their business.

    In theory r:* will auto-deduce the correct format.
    """
    try:
        mode = f"r:{context['tarFormat']}"
    except KeyNotInContextError:
        mode = 'r:*'

    return mode


def get_file_mode_for_writing(context):
    """Get file mode for writing from context['tarFormat']

    This should return w:, w:gz, w:bz2 or w:xz. If user specified something
    wacky in tarFormat, that's their business.
    """
    try:
        mode = f"w:{context['tarFormat']}"
    except KeyNotInContextError:
        mode = 'w:xz'

    return mode


def tar_archive(context):
    """Archive specified path to a tar archive.

    Args:
        context: dictionary-like. context is mandatory.
            context['tarArchive'] must exist. It's a dictionary.
            keys are the paths to archive.
            values are the destination output paths.

    Example:
        tarArchive:
            - in: path/to/dir
              out: path/to/destination.tar.xs
            - in: another/my.file
              out: ./my.tar.xs

        This will archive directory path/to/dir to path/to/destination.tar.xs,
        and also archive file another/my.file to ./my.tar.xs
    """
    logger.debug("start")

    mode = get_file_mode_for_writing(context)

    for item in context['tarArchive']:
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
            context['tarExtract'] must exist. It's a dictionary.
            keys are the path to the tar to extract.
            values are the destination paths.

    Example:
        tarExtract:
            - in: path/to/my.tar.xs
              out: /path/extract/here
            - in: another/tar.xs
              out: .

        This will extract path/to/my.tar.xs to /path/extract/here, and also
        extract another/tar.xs to $PWD.
    """
    logger.debug("start")

    mode = get_file_mode_for_reading(context)

    for item in context['tarExtract']:
        # in is the path to the tar to extract. Allows string interpolation.
        source = context.get_formatted_string(item['in'])
        # out is the outdir, dhur. Allows string interpolation.
        destination = context.get_formatted_string(item['out'])
        with tarfile.open(source, mode) as extract_me:
            logger.debug(f"Extracting '{source}' to '{destination}'")

            extract_me.extractall(destination)
            logger.info(f"Extracted '{source}' to '{destination}'")

    logger.debug("end")
