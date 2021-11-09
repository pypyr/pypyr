"""fileloader.py unit tests."""
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from pypyr.errors import PipelineNotFoundError
import pypyr.loaders.file as fileloader
from pypyr.pipedef import PipelineDefinition, PipelineFileInfo

# region get_pipeline_path

cwd = Path.cwd()
cwd_tests = cwd.joinpath('tests')
pypyr_path = cwd.joinpath('pypyr', 'pipelines')


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
    with (patch('pypyr.loaders.file.CWD',
                new=cwd_tests),
          patch('pypyr.loaders.file.cwd_pipelines_dir',
          new=cwd_tests.joinpath('pipelines'))):
        path_found = fileloader.get_pipeline_path('testpipeline', None)

    expected_path = cwd_tests.joinpath('pipelines', 'testpipeline.yaml')

    assert path_found == expected_path


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


@patch('ruamel.yaml.YAML.load', return_value='mocked pipeline def')
@patch('pypyr.loaders.file.get_pipeline_path',
       return_value=Path('arb/path/x.yaml'))
def test_get_pipeline_definition_pass(mocked_get_path,
                                      mocked_yaml):
    """get_pipeline_definition passes correct params to all methods."""
    with patch('pypyr.loaders.file.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        pipeline_def = fileloader.get_pipeline_definition(
            'pipename', '/parent/dir')

    assert pipeline_def == PipelineDefinition(
        'mocked pipeline def',
        PipelineFileInfo(pipeline_name='pipename',
                         loader=None,
                         parent='/parent/dir',
                         path=Path('arb/path/x.yaml')))

    mocked_get_path.assert_called_once_with(pipeline_name='pipename',
                                            parent='/parent/dir')
    mocked_open.assert_called_once_with(Path('arb/path/x.yaml'))
    mocked_yaml.assert_called_once_with(mocked_open.return_value)


@patch('pypyr.loaders.file.get_pipeline_path',
       return_value=Path('arb/path/x.yaml'))
def test_get_pipeline_definition_file_not_found(mocked_get_path):
    """get_pipeline_definition raises file not found."""
    fileloader._file_cache.clear()
    with patch('pypyr.loaders.file.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        mocked_open.side_effect = FileNotFoundError('deliberate err')
        with pytest.raises(FileNotFoundError):
            fileloader.get_pipeline_definition('pipename', '/arb/dir')

    mocked_get_path.assert_called_once_with(pipeline_name='pipename',
                                            parent='/arb/dir')

    fileloader._file_cache.clear()
# endregion get_pipeline_definition
