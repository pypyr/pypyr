"""fileloader.py unit tests."""
from pathlib import Path
from unittest.mock import mock_open, patch
from pypyr.errors import PipelineNotFoundError
import pypyr.pypeloaders.fileloader
import pytest


# ------------------------- get_pipeline_path --------------------------------#

cwd = Path.cwd()


def test_get_pipeline_path_in_working_dir():
    """Find a pipeline in the working dir"""
    working_dir = cwd.joinpath('tests')
    path_found = pypyr.pypeloaders.fileloader.get_pipeline_path(
        'testpipelinewd',
        working_dir)

    expected_path = cwd.joinpath('tests',
                                 'testpipelinewd.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_in_working_dir_pipelines():
    """Find a pipeline in the working dir pipelines"""
    working_dir = cwd.joinpath('tests')
    path_found = pypyr.pypeloaders.fileloader.get_pipeline_path('testpipeline',
                                                                working_dir)

    expected_path = cwd.joinpath('tests',
                                 'pipelines',
                                 'testpipeline.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_in_pypyr_dir():
    """Find a pipeline in the pypyr install dir"""
    working_dir = cwd.joinpath('tests')
    path_found = pypyr.pypeloaders.fileloader.get_pipeline_path('donothing',
                                                                working_dir)

    expected_path = cwd.joinpath('pypyr',
                                 'pipelines',
                                 'donothing.yaml')

    assert path_found == expected_path


def test_get_pipeline_path_raises():
    """Failure to find pipeline should raise PipelineNotFoundError"""
    with pytest.raises(PipelineNotFoundError) as err:
        pypyr.pypeloaders.fileloader.get_pipeline_path('unlikelypipeherexyz',
                                                       cwd)

    current_path = cwd.joinpath('pipelines')

    pypyr_path = cwd.joinpath('pypyr',
                              'pipelines')

    expected_msg = (
        f'unlikelypipeherexyz.yaml not found in any of the following:\n'
        f'{cwd}\n{current_path}\n{pypyr_path}')

    assert str(err.value) == f"{expected_msg}"


# ------------------------- get_pipeline_path --------------------------------#

# ------------------------- get_pipeline_definition --------------------------#

@patch('ruamel.yaml.YAML.load', return_value='mocked pipeline def')
@patch('pypyr.pypeloaders.fileloader.get_pipeline_path',
       return_value='arb/path/x.yaml')
def test_get_pipeline_definition_pass(mocked_get_path,
                                      mocked_yaml):
    """get_pipeline_definition passes correct params to all methods."""
    with patch('pypyr.pypeloaders.fileloader.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        pipeline_def = pypyr.pypeloaders.fileloader.get_pipeline_definition(
            'pipename', '/working/dir')

    assert pipeline_def == 'mocked pipeline def'
    mocked_get_path.assert_called_once_with(
        pipeline_name='pipename', working_directory='/working/dir')
    mocked_open.assert_called_once_with('arb/path/x.yaml')
    mocked_yaml.assert_called_once_with(mocked_open.return_value)


@patch('pypyr.pypeloaders.fileloader.get_pipeline_path',
       return_value='arb/path/x.yaml')
def test_get_pipeline_definition_file_not_found(mocked_get_path):
    """get_pipeline_definition raises file not found."""
    with patch('pypyr.pypeloaders.fileloader.open',
               mock_open(read_data='pipe contents')) as mocked_open:
        mocked_open.side_effect = FileNotFoundError('deliberate err')
        with pytest.raises(FileNotFoundError):
            pypyr.pypeloaders.fileloader.get_pipeline_definition(
                'pipename', '/working/dir')

# ------------------------- get_pipeline_definition --------------------------#
