from unittest.mock import call

# the entire point is to test imports when import package, even when not used.
import pypyr  # noqa: F401
from tests.common.utils import patch_logger


def test_init_package():
    """Import pypyr runs one off initialization code."""
    import logging
    with patch_logger(__name__, logging.NOTIFY) as mock_log:
        logging.getLogger(__name__).notify("arb")

    assert mock_log.mock_calls == [call('arb')]
