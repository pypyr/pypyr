"""pipelinecache.py unit tests."""
import pytest
from unittest.mock import MagicMock, patch
from pypyr.errors import PipelineNotFoundError
import pypyr.cache.pipelinecache as pipelinecache
import pypyr.cache.loadercache as loadercache
from pypyr.moduleloader import get_working_directory
# ------------------------- load_pipeline --------------------------------#


def test_load_pipeline_module_not_found():
    """Module not found raises."""
    with pytest.raises(PipelineNotFoundError):
        pipelinecache.load_pipeline(pipeline_name='blah-blah-unlikely-name')()


def test_load_pipeline_attr_not_found_on_loader():
    """Attribute not found raises."""
    with pytest.raises(AttributeError):
        pipelinecache.load_pipeline(pipeline_name="blah", loader=__name__)()


def test_load_pipeline_ok():
    """Pipeline loads with default loader."""
    loadercache.pypeloader_cache.clear()
    pipelinecache.pipeline_cache.clear()

    get_pipe_def = MagicMock()
    get_pipe_def.return_value = "test"

    with patch('pypyr.cache.loadercache.load_the_loader') as mock_loader:
        mock_loader.return_value = get_pipe_def
        response = pipelinecache.load_pipeline(pipeline_name='arb',
                                               loader='arbxloader')()

    assert response == "test"
    mock_loader.assert_called_once_with('arbxloader')
    get_pipe_def.assert_called_once_with(pipeline_name='arb',
                                         working_dir=get_working_directory())
# ------------------------- END load_pipeline ----------------------------#

# ------------------------- PipelineCache --------------------------------#

# ------------------------- PipeLineCache: get_pipeline ------------------#


def test_get_pipeline_default():
    """Get Pipeline's defaults to filepipeline loader."""
    with patch('pypyr.cache.pipelinecache.load_pipeline') as mock:
        mock.return_value = lambda: "arbtest"
        p = pipelinecache.PipelineCache().get_pipeline("arbpipeline")

    mock.assert_called_once_with('arbpipeline', None)
    assert p == "arbtest"


def test_get_pipeline_specified_loader():
    """Get pipeline passes arg to loader."""
    with patch('pypyr.cache.pipelinecache.load_pipeline') as mock:
        mock.return_value = lambda: "arbtest"
        p = pipelinecache.PipelineCache().get_pipeline("arbpipeline",
                                                       "loaderx")

    mock.assert_called_once_with('arbpipeline', 'loaderx')
    assert p == "arbtest"
# ------------------------- PipeLineCache: get_pipeline -------------------#

# ------------------------- END PipelineCache -----------------------------#
