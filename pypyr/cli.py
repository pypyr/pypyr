"""cli entry point for pipeline runner.

Parse command line arguments in, invoke pipelinerunner.
"""
import argparse
import os
import pypyr.pipelinerunner
import pypyr.version
import signal
import sys


def get_args():
    """Parse arguments passed in from shell."""
    parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='pypyr pipeline runner')
    parser.add_argument('--name', dest='pipeline_name', required=True,
                        help='Name of pipeline to run. It should exist in the '
                        '/pipelines directory.')
    parser.add_argument('--context', dest='pipeline_context',
                        help='String for context values. Parsed by '
                        'pipeline''s context_parser function.')
    parser.add_argument('--dir', dest='working_dir', default=os.getcwd(),
                        help='Working directory. Use if your pipelines '
                        'directory is elsewhere. Defaults to cwd.')
    parser.add_argument('--loglevel', dest='log_level', type=int, default=20,
                        help='Integer log level. Defaults to 10 (Debug). '
                        '10=DEBUG 20=INFO 30=WARNING 40=ERROR 50=CRITICAL')
    parser.add_argument('--version', action='version',
                        help='Echo version number.',
                        version=f'{pypyr.version.get_version()}')

    return parser.parse_args()


def main():
    """Entry point for pypyr cli.

    The setup_py entry_point wraps this in sys.exit already so this effectively
    becomes sys.exit(main()).
    The __main__ entry point similarly wraps sys.exit().
    """
    args = get_args()

    try:
        return pypyr.pipelinerunner.main(
            pipeline_name=args.pipeline_name,
            pipeline_context_input=args.pipeline_context,
            working_dir=args.working_dir,
            log_level=args.log_level)
    except KeyboardInterrupt:
        # Shell standard is 128 + signum = 130 (SIGINT = 2)
        sys.stdout.write("\n")
        return 128 + signal.SIGINT
    except Exception as e:
        # stderr and exit code 255
        sys.stderr.write("\n")
        sys.stderr.write(f"\033[91m{type(e).__name__}: {str(e)}")
        sys.stderr.write("\n")
        return 255
