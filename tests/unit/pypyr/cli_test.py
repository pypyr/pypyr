"""cli.py unit tests."""
import os
import pypyr.cli
import pytest
from unittest.mock import patch


def test_main_pass_with_sysargv():
    """Invoke from cli sets sys.argv, check assigns correctly to args."""
    arg_list = ['pypyr',
                'blah',
                '--log',
                '50',
                '--context',
                'ctx string',
                '--dir',
                'dir here']

    with patch('sys.argv', arg_list):
        with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
            pypyr.cli.main()

        mock_pipeline_main.assert_called_once_with(
            pipeline_name='blah',
            pipeline_context_input='ctx string',
            working_dir='dir here',
            log_level=50
        )


def test_main_pass_with_defaults():
    """Default values assigned - log 20 and cwd"""
    arg_list = ['blah',
                '--context',
                'ctx string']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        pypyr.cli.main(arg_list)

    mock_pipeline_main.assert_called_once_with(
        pipeline_name='blah',
        pipeline_context_input='ctx string',
        working_dir=os.getcwd(),
        log_level=20
    )


def test_pipeline_name_required():
    """Error expected if no pipeline name"""
    arg_list = ['--context',
                'ctx string']

    with patch('pypyr.pipelinerunner.main'):
        with pytest.raises(SystemExit) as exit_err:
            pypyr.cli.main(arg_list)

        print(exit_err.value)
        assert exit_err.value.code == 2


def test_interrupt_signal():
    """Interrupt signal handled."""
    arg_list = ['blah',
                '--context',
                'ctx string']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        mock_pipeline_main.side_effect = KeyboardInterrupt()
        val = pypyr.cli.main(arg_list)
        assert val == 130


def test_arb_error():
    """Arbitrary error should return 255."""
    arg_list = ['blah',
                '--context',
                'ctx string']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        mock_pipeline_main.side_effect = AssertionError('Test Error Mock')
        val = pypyr.cli.main(arg_list)
        assert val == 255
