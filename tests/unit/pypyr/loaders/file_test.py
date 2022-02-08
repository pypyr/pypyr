"""fileloader.py unit tests."""
from pathlib import Path
from unittest.mock import call, mock_open, patch, PropertyMock

import pytest

from pypyr.errors import PipelineNotFoundError
import pypyr.loaders.file as fileloader
from pypyr.pipedef import PipelineDefinition, PipelineFileInfo

# region get_pipeline_path

cwd = Path.cwd()
cwd_tests = cwd.joinpath('tests')
pypyr_path = cwd.joinpath('pypyr', 'pipelines')


def test_get_pipeline_path_absolute_path():
    """Find a pipeline with absolute path."""
    abs_path = Path('tests/testpipelinewd.yaml').resolve()
    str_abs_sans_yaml = str(abs_path.with_suffix(''))

    path_found = fileloader.get_pipeline_path(str_abs_sans_yaml, None)

    expected_path = cwd_tests.joinpath('testpipelinewd.yaml')
    assert path_found == expected_path


def test_get_pipeline_path_absolute_path_ignore_parent():
    """Find a pipeline with absolute path ignore parent input."""
    abs_path = Path('tests/testpipelinewd.yaml').resolve()
    str_abs_sans_yaml = str(abs_path.with_suffix(''))

    path_found = fileloader.get_pipeline_path(str_abs_sans_yaml, 'parent')

    expected_path = cwd_tests.joinpath('testpipelinewd.yaml')
    assert path_found == expected_path


def test_get_pipeline_path_absolute_path_not_found():
    """Error when can't find pipeline with absolute path."""
    abs_path = Path('tests/XXXZZZ.yaml').resolve()
    str_abs_sans_yaml = str(abs_path.with_suffix(''))

    with pytest.raises(PipelineNotFoundError) as err:
        fileloader.get_pipeline_path(str_abs_sans_yaml, None)

    assert str(err.value) == f'{abs_path} does not exist.'


def test_get_pipeline_path_no_parent():
    """Find a pipeline in the working dir when no parent."""
    path_found = fileloader.get_pipeline_path(
        'tests/testpipelinewd', None)

    expected_path = cwd_tests.joinpath('testpipelinewd.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_in_parent():
    """Find a pipeline in the parent dir pipelines."""
    path_found = fileloader.get_pipeline_path('testpipeline',
                                              'tests/pipelines')

    expected_path = cwd_tests.joinpath('pipelines',
                                       'testpipeline.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_in_cwd_pipelines():
    """Find a pipeline in cwd/pipelines."""
    # artificially change the cwd constant
    # when py 3.10 can use () instead of \ for multiline "with"
    with patch('pypyr.config.Config.cwd',
               new_callable=PropertyMock(return_value=cwd_tests)), \
        patch('pypyr.loaders.file.cwd_pipelines_dir',
              new=cwd_tests.joinpath('pipelines')):
        path_found = fileloader.get_pipeline_path('testpipeline', None)

    assert path_found == cwd_tests.joinpath('pipelines', 'testpipeline.yaml')


def test_get_pipeline_path_in_pypyr_dir():
    """Find a pipeline in the pypyr install dir."""
    path_found = fileloader.get_pipeline_path('donothing',
                                              'tests')

    expected_path = cwd.joinpath('pypyr',
                                 'pipelines',
                                 'donothing.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_raises_with_parent_doesnt_exist():
    """Raise PipelineNotFoundError no pipeline found, non-existing parent."""
    with pytest.raises(PipelineNotFoundError) as err:
        fileloader.get_pipeline_path('unlikelypipeherexyz',
                                     'unlikelyparentxyz')

    cwd_pipes_path = cwd.joinpath('pipelines')

    expected_msg = (
        f'unlikelypipeherexyz.yaml not found in any of the following:\n'
        f'{cwd}\n{cwd_pipes_path}\n{pypyr_path}')

    assert str(err.value) == expected_msg


def test_get_pipeline_path_raises_with_parent_exists():
    """Raise PipelineNotFoundError no pipeline found, existing parent."""
    with pytest.raises(PipelineNotFoundError) as err:
        fileloader.get_pipeline_path('unlikelypipeherexyz',
                                     'tests/pipelines')

    parent = cwd.joinpath('tests/pipelines')
    cwd_pipes_path = cwd.joinpath('pipelines')

    expected_msg = (
        f'unlikelypipeherexyz.yaml not found in any of the following:\n'
        f'{parent}\n{cwd}\n{cwd_pipes_path}\n{pypyr_path}')

    assert str(err.value) == expected_msg


def test_get_pipeline_path_raises_no_parent():
    """Failure to find pipeline raises PipelineNotFoundError, no parent."""
    with pytest.raises(PipelineNotFoundError) as err:
        fileloader.get_pipeline_path('unlikelypipeherexyz',
                                     None)

    cwd_pipes_path = cwd.joinpath('pipelines')

    expected_msg = (
        f'unlikelypipeherexyz.yaml not found in any of the following:\n'
        f'{cwd}\n{cwd_pipes_path}\n{pypyr_path}')

    assert str(err.value) == expected_msg


def test_get_pipeline_path_raises_parent_is_cwd():
    """Raise PipelineNotFoundError on not found when parent == cwd."""
    with pytest.raises(PipelineNotFoundError) as err:
        fileloader.get_pipeline_path('unlikelypipeherexyz',
                                     Path.cwd())

    cwd_pipes_path = cwd.joinpath('pipelines')

    expected_msg = (
        f'unlikelypipeherexyz.yaml not found in any of the following:\n'
        f'{cwd}\n{cwd_pipes_path}\n{pypyr_path}')

    assert str(err.value) == expected_msg

# endregion get_pipeline_path

# region get_pipeline_definition


@patch('pypyr.loaders.file.add_sys_path')
@patch('ruamel.yaml.YAML.load', return_value='mocked pipeline def')
@patch('pypyr.loaders.file.get_pipeline_path',
       return_value=Path('arb/path/x.yaml'))
def test_get_pipeline_definition_pass(mocked_get_path,
                                      mocked_yaml,
                                      mocked_add_sys):
    """get_pipeline_definition passes correct params to all methods."""
    fileloader._file_cache.clear()

    with patch('pypyr.loaders.file.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        pipeline_def = fileloader.get_pipeline_definition(
            'pipename', '/parent/dir')

    assert pipeline_def == PipelineDefinition(
        'mocked pipeline def',
        PipelineFileInfo(pipeline_name='x.yaml',
                         loader='pypyr.loaders.file',
                         parent=Path('arb/path'),
                         path=Path('arb/path/x.yaml')))

    path = Path('arb/path/x.yaml')
    mocked_get_path.assert_called_once_with(pipeline_name='pipename',
                                            parent='/parent/dir')
    mocked_open.assert_called_once_with(path, encoding=None)
    mocked_yaml.assert_called_once_with(mocked_open.return_value)
    assert fileloader._file_cache._cache == {str(path): pipeline_def}
    mocked_add_sys.assert_called_once_with(Path('arb/path'))

    fileloader._file_cache.clear()


@patch('pypyr.loaders.file.add_sys_path')
@patch('ruamel.yaml.YAML.load', return_value='mocked pipeline def')
@patch('pypyr.loaders.file.get_pipeline_path',
       return_value=Path('arb/path/x.yaml'))
def test_get_pipeline_definition_from_cache(mocked_get_path,
                                            mocked_yaml,
                                            mocked_add_sys):
    """Known path returns from cache."""
    fileloader._file_cache.clear()

    with patch('pypyr.loaders.file.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        pipeline_def_1 = fileloader.get_pipeline_definition(
            'pipename', '/parent/dir')
        pipeline_def_2 = fileloader.get_pipeline_definition(
            'pipename', '/parent/dir')

    assert pipeline_def_1 == pipeline_def_2 == PipelineDefinition(
        'mocked pipeline def',
        PipelineFileInfo(pipeline_name='x.yaml',
                         loader='pypyr.loaders.file',
                         parent=Path('arb/path'),
                         path=Path('arb/path/x.yaml')))

    # get path called X2, everything subsequent X1
    mocked_get_path.mock_calls == [
        call(pipeline_name='pipename', parent='/parent/dir'),
        call(pipeline_name='pipename', parent='/parent/dir')]

    path = Path('arb/path/x.yaml')
    mocked_open.assert_called_once_with(path, encoding=None)
    mocked_yaml.assert_called_once_with(mocked_open.return_value)
    mocked_add_sys.assert_called_once_with(Path('arb/path'))

    assert fileloader._file_cache._cache == {str(path): pipeline_def_1}
    assert fileloader._file_cache._cache[str(path)] is pipeline_def_1

    fileloader._file_cache.clear()


@patch('pypyr.loaders.file.add_sys_path')
@patch('ruamel.yaml.YAML.load', return_value='mocked pipeline def')
@patch('pypyr.loaders.file.get_pipeline_path',
       return_value=Path('arb/path/x.yaml'))
def test_get_pipeline_definition_with_encoding(mocked_get_path,
                                               mocked_yaml,
                                               mocked_add_sys):
    """Open pipeline with custom encoding."""
    fileloader._file_cache.clear()

    with patch('pypyr.loaders.file.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        with patch('pypyr.config.config.default_encoding', 'arb'):
            pipeline_def = fileloader.get_pipeline_definition(
                'pipename', '/parent/dir')

    assert pipeline_def == PipelineDefinition(
        'mocked pipeline def',
        PipelineFileInfo(pipeline_name='x.yaml',
                         loader='pypyr.loaders.file',
                         parent=Path('arb/path'),
                         path=Path('arb/path/x.yaml')))

    mocked_get_path.assert_called_once_with(pipeline_name='pipename',
                                            parent='/parent/dir')
    path = Path('arb/path/x.yaml')
    mocked_open.assert_called_once_with(path, encoding='arb')
    assert fileloader._file_cache._cache == {str(path): pipeline_def}
    mocked_yaml.assert_called_once_with(mocked_open.return_value)
    mocked_add_sys.assert_called_once_with(Path('arb/path'))
    fileloader._file_cache.clear()


@patch('pypyr.loaders.file.add_sys_path')
@patch('pypyr.loaders.file.get_pipeline_path',
       return_value=Path('arb/path/x.yaml'))
def test_get_pipeline_definition_file_not_found(mocked_get_path,
                                                mocked_add_sys_path):
    """get_pipeline_definition raises file not found."""
    fileloader._file_cache.clear()

    with patch('pypyr.loaders.file.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        mocked_open.side_effect = FileNotFoundError('deliberate err')
        with pytest.raises(FileNotFoundError):
            fileloader.get_pipeline_definition('pipename', '/arb/dir')

    mocked_get_path.assert_called_once_with(pipeline_name='pipename',
                                            parent='/arb/dir')

    assert fileloader._file_cache._cache == {}
    mocked_add_sys_path.assert_not_called()

    fileloader._file_cache.clear()
# endregion get_pipeline_definition
