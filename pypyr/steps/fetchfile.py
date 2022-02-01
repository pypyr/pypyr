"""pypyr step that fetch files from URL"""
import logging

from pypyr.utils.fetch import file_get
from pypyr.utils.asserts import assert_keys_are_truthy

logger = logging.getLogger(__name__)


def run_step(context):
    """Fetch files from URL.
   It is used for fetching files from http, https, ftp, sftp.
   Supported http basic auth, ftp and sftp auth.
    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context key must exist
                - fetchFile
                    - path. path-like. Path to file on disk.
                    - url. string. URL should be in the form
                    <proto>://<site>[:port]<path>
                    Examples:
                        http://www.example.com/files/file.tar.gz
                        https://www.example.com/files/file.tar.gz
                        ftp://ftp.example.com/files/file.tar.gz
                        ftp://username:password@ftp.example.com/files/file.tar.gz
                        sftp://username:password@ftp.example.com/files/file.tar.gz

    Returns:
        None. Downloads remote file.
    Raises:
        pypyr.errors.KeyNotInContextError: fetchFile,
        fetchFile['path'], fetchFile['url']  missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fetchFile,
        fetchFile['path'], fetchFile['url'] exists but is None.
    """
    logger.debug("started")

    context.assert_key_has_value(key='fetchFile', caller=__name__)

    fetch_file_input = context.get_formatted('fetchFile')

    assert_keys_are_truthy(obj=fetch_file_input,
                           keys=('url', 'path'),
                           caller=__name__,
                           parent='fetchFile')

    base_url = fetch_file_input['url']
    dest_path = fetch_file_input['path']

    fetching = file_get(base_url, dest_path)

    logger.info(fetching)
    logger.debug("done")
