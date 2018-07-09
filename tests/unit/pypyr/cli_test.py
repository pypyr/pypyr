"""cli.py unit tests."""
import os
import pypyr.cli
import pytest
from unittest.mock import patch


def test_main_pass_with_sysargv_context_positional():
    """Invoke from cli sets sys.argv, check assigns correctly to args."""
    arg_list = ['pypyr',
                'blah',
                'ctx string',
                '--log',
                '50',
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


def test_main_pass_with_sysargv_context_positional_flags_last():
    """Check assigns correctly to args when positional last not first."""
    arg_list = ['pypyr',
                '--log',
                '50',
                '--dir',
                'dir here',
                'blah',
                'ctx string', ]

    with patch('sys.argv', arg_list):
        with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
            pypyr.cli.main()

        mock_pipeline_main.assert_called_once_with(
            pipeline_name='blah',
            pipeline_context_input='ctx string',
            working_dir='dir here',
            log_level=50
        )


def test_main_pass_with_defaults_context_positional():
    """Default values assigned - log 20 and cwd"""
    arg_list = ['blah',
                'ctx string']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        pypyr.cli.main(arg_list)

    mock_pipeline_main.assert_called_once_with(
        pipeline_name='blah',
        pipeline_context_input='ctx string',
        working_dir=os.getcwd(),
        log_level=20
    )


def test_main_pass_with_no_context():
    """No context is None."""
    arg_list = ['blah']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        pypyr.cli.main(arg_list)

    mock_pipeline_main.assert_called_once_with(
        pipeline_name='blah',
        pipeline_context_input=None,
        working_dir=os.getcwd(),
        log_level=20
    )


def test_main_pass_with_no_context_other_flags_set():
    """No context is None and other flag still work."""
    arg_list = ['blah',
                '--log',
                '11']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        pypyr.cli.main(arg_list)

    mock_pipeline_main.assert_called_once_with(
        pipeline_name='blah',
        pipeline_context_input=None,
        working_dir=os.getcwd(),
        log_level=11
    )


def test_pipeline_name_required():
    """Error expected if no pipeline name"""
    arg_list = ['--dir',
                'blah']

    with patch('pypyr.pipelinerunner.main'):
        with pytest.raises(SystemExit) as exit_err:
            pypyr.cli.main(arg_list)

        print(exit_err.value)
        assert exit_err.value.code == 2


def test_interrupt_signal():
    """Interrupt signal handled."""
    arg_list = ['blah',
                'ctx string']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        mock_pipeline_main.side_effect = KeyboardInterrupt()
        val = pypyr.cli.main(arg_list)
        assert val == 130


def test_arb_error():
    """Arbitrary error should return 255."""
    arg_list = ['blah',
                'ctx string']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        mock_pipeline_main.side_effect = AssertionError('Test Error Mock')
        val = pypyr.cli.main(arg_list)
        assert val == 255


def test_trace_log_level():
    """Log Level < 10 produces traceback on error."""
    arg_list = ['blah',
                'ctx string',
                '--log',
                '5']

    with patch('pypyr.pipelinerunner.main') as mock_pipeline_main:
        with patch('traceback.print_exc') as mock_traceback:
            mock_pipeline_main.side_effect = AssertionError('Test Error Mock')
            val = pypyr.cli.main(arg_list)
            assert val == 255

    mock_traceback.assert_called_once()
