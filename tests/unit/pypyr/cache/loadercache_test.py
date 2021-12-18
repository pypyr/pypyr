"""loadercache.py unit tests."""
from unittest.mock import call, patch, Mock

import pytest

import pypyr.cache.loadercache as loadercache
from pypyr.errors import (PipelineDefinitionError,
                          PipelineNotFoundError,
                          PyModuleNotFoundError)
from pypyr.pipedef import PipelineDefinition, PipelineInfo


# region load_the_loader


def test_load_the_loader_module_not_found():
    """Module not found raises."""
    with pytest.raises(PyModuleNotFoundError):
        loadercache.load_the_loader('blah-blah-unlikely-name')


def test_load_the_loader_attr_not_found():
    """Attribute not found raises."""
    with pytest.raises(AttributeError):
        loadercache.load_the_loader(__name__)


def test_load_the_loader_ok():
    """Module with attribute returns function."""
    loader = loadercache.load_the_loader('tests.arbpack.arbloader')
    assert isinstance(loader, loadercache.Loader)
    assert loader.name == 'tests.arbpack.arbloader'
    response = loader.get_pipeline(name='arb', parent='/arb')

    assert response == PipelineDefinition(
        pipeline={'pipeline_name': 'arb', 'parent': '/arb'},
        info=PipelineInfo('arb', 'tests.arbpack.arbloader', '/arb'))

    # 2nd time gets from cache
    response2 = loader.get_pipeline(name='arb', parent='/arb')
    assert response == response2
    assert response is response2
    assert len(loader._pipeline_cache._cache) == 1

    # name+parent is unique
    response3 = loader.get_pipeline(name='arb', parent='/arb2')
    assert response3 == PipelineDefinition(
        pipeline={'pipeline_name': 'arb', 'parent': '/arb2'},
        info=PipelineInfo('arb', 'tests.arbpack.arbloader', '/arb2'))
    assert len(loader._pipeline_cache._cache) == 2

    response4 = loader.get_pipeline(name='arb2', parent='/arb2')
    assert response4 == PipelineDefinition(
        pipeline={'pipeline_name': 'arb2', 'parent': '/arb2'},
        info=PipelineInfo('arb2', 'tests.arbpack.arbloader', '/arb2'))
    assert len(loader._pipeline_cache._cache) == 3

    response5 = loader.get_pipeline(name='arb2', parent=None)
    assert response5 == PipelineDefinition(
        pipeline={'pipeline_name': 'arb2', 'parent': None},
        info=PipelineInfo('arb2', 'tests.arbpack.arbloader', None))
    assert len(loader._pipeline_cache._cache) == 4


def test_pipeline_not_found_by_loader():
    """Pipeline not found raises."""
    with pytest.raises(PipelineNotFoundError):
        loadercache.LoaderCache().get_pype_loader().get_pipeline(
            name='blah-blah-unlikely-name',
            parent=None)

# endregion load_the_loader

# region LoaderCache

# region LoaderCache: get_pype_loader


def test_get_pype_loader_default():
    """Loader defaults to fileloader."""
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        mock_get_def.return_value = Mock(spec=dict())
        mock_get_module.return_value.get_pipeline_definition = mock_get_def
        loader = loadercache.LoaderCache().get_pype_loader()

    mock_get_module.assert_called_once_with('pypyr.loaders.file')
    assert loader.name == 'pypyr.loaders.file'

    loader.get_pipeline('arb', 'parent')
    mock_get_def.assert_called_once_with(pipeline_name='arb', parent='parent')


def test_get_pype_loader_specified_returning_pipe_def():
    """Loader passes loader arg and works with returned PipelineDefinition."""
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        mock_get_def.return_value = PipelineDefinition(
            pipeline={'my': 'pipe'},
            info=PipelineInfo('pipename', 'arbloader', 'parent'))

        mock_get_module.return_value.get_pipeline_definition = mock_get_def
        loader = loadercache.LoaderCache().get_pype_loader('arbloader')

    mock_get_module.assert_called_once_with('arbloader')
    assert loader.name == 'arbloader'

    pipeline = loader.get_pipeline('arb', None)
    assert pipeline == PipelineDefinition(
        pipeline={'my': 'pipe'},
        info=PipelineInfo('pipename', 'arbloader', 'parent'))
    mock_get_def.assert_called_once_with(pipeline_name='arb', parent=None)


def test_get_pype_loader_specified_wraps_in_pipedef():
    """Loader passes loader arg and wraps response in PipelineDefinition."""
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        mock_get_def.return_value = {'a': 'b'}

        mock_get_module.return_value.get_pipeline_definition = mock_get_def
        loader = loadercache.LoaderCache().get_pype_loader('arbloader')

    mock_get_module.assert_called_once_with('arbloader')
    assert loader.name == 'arbloader'

    pipeline = loader.get_pipeline('arb', 'parent')
    assert pipeline == PipelineDefinition(
        pipeline={'a': 'b'},
        info=PipelineInfo('arb', 'arbloader', 'parent'))

    mock_get_def.assert_called_once_with(pipeline_name='arb', parent='parent')


def test_get_pype_loader_specified_raises_error_on_bad_yaml():
    """Raise error on get_pipeline where top-level yaml malformed."""
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        # top-level yaml must be a dict, not a list.
        mock_get_def.return_value = ['a', 'b']

        mock_get_module.return_value.get_pipeline_definition = mock_get_def
        loader = loadercache.LoaderCache().get_pype_loader('arbloader')

    mock_get_module.assert_called_once_with('arbloader')
    assert loader.name == 'arbloader'

    with pytest.raises(PipelineDefinitionError):
        loader.get_pipeline('arb', 'parent')

    mock_get_def.assert_called_once_with(pipeline_name='arb', parent='parent')
# endregion LoaderCache: get_pype_loader

# region LoaderCache: clear_pipes


def test_loader_clear():
    """Clear pipeline cache in Loader."""
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        mock_get_def.return_value = Mock(spec=dict())

        mock_get_module.return_value.get_pipeline_definition = mock_get_def
        loader = loadercache.LoaderCache().get_pype_loader('arbloader')

    mock_get_module.assert_called_once_with('arbloader')
    assert loader.name == 'arbloader'

    loader.get_pipeline('arb', None)
    loader.get_pipeline('arb2', None)

    assert mock_get_def.mock_calls == [call(pipeline_name='arb', parent=None),
                                       call(pipeline_name='arb2', parent=None)]

    assert len(loader._pipeline_cache._cache) == 2
    loader.clear()
    assert len(loader._pipeline_cache._cache) == 0


def test_loadercache_clear_pipes():
    """Clear pipeline cache in LoaderCache."""
    lc = loadercache.LoaderCache()
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        mock_get_def.return_value = Mock(spec=dict())
        mock_get_module.return_value.get_pipeline_definition = mock_get_def

        arb_loader = lc.get_pype_loader('arbloader')
        arb_loader2 = lc.get_pype_loader('arbloader2')

    mock_get_module.assert_any_call('arbloader')
    mock_get_module.assert_any_call('arbloader2')

    arb_loader.get_pipeline('arb', None)
    arb_loader.get_pipeline('arb2', None)

    arb_loader2.get_pipeline('arb3', None)

    assert mock_get_def.mock_calls == [call(pipeline_name='arb', parent=None),
                                       call(pipeline_name='arb2', parent=None),
                                       call(pipeline_name='arb3', parent=None)]

    assert len(arb_loader._pipeline_cache._cache) == 2
    assert len(arb_loader2._pipeline_cache._cache) == 1

    lc.clear_pipes('arbloader')

    assert len(arb_loader._pipeline_cache._cache) == 0
    assert len(arb_loader2._pipeline_cache._cache) == 1

    # unknown loader name doesn't error
    arb_loader.get_pipeline('arb', None)
    lc.clear_pipes('doesntexist')
    assert len(arb_loader._pipeline_cache._cache) == 1
    assert len(arb_loader2._pipeline_cache._cache) == 1


def test_loadercache_clear_pipes_all():
    """Clear all pipeline cache in LoaderCache."""
    lc = loadercache.LoaderCache()
    with patch('pypyr.moduleloader.get_module') as mock_get_module:
        mock_get_def = Mock()
        mock_get_def.return_value = Mock(spec=dict())
        mock_get_module.return_value.get_pipeline_definition = mock_get_def
        arb_loader = lc.get_pype_loader('arbloader')
        arb_loader2 = lc.get_pype_loader('arbloader2')

    mock_get_module.mock_calls == [call('arbloader'), call('arbloader2')]

    arb_loader.get_pipeline('arb', None)
    arb_loader.get_pipeline('arb2', None)

    arb_loader2.get_pipeline('arb3', None)

    assert mock_get_def.mock_calls == [call(pipeline_name='arb', parent=None),
                                       call(pipeline_name='arb2', parent=None),
                                       call(pipeline_name='arb3', parent=None)]

    assert len(arb_loader._pipeline_cache._cache) == 2
    assert len(arb_loader2._pipeline_cache._cache) == 1

    lc.clear_pipes()

    assert len(arb_loader._pipeline_cache._cache) == 0
    assert len(arb_loader2._pipeline_cache._cache) == 0
# endregion LoaderCache: clear_pipes
# endregion LoaderCache
