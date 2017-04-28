"""cli entry point for pipeline runner.

Parse command line arguments in, invoke pipelinerunner.
"""
import argparse
import os
import pypyr.pipelinerunner
import pypyr.version
import signal
import sys
import traceback


def get_args(args):
    """Parse arguments passed in from shell."""
    return get_parser().parse_args(args)


def get_parser():
    """Return ArgumentParser for pypyr cli."""
    parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='pypyr pipeline runner')
    parser.add_argument('pipeline_name',
                        help='Name of pipeline to run. It should exist in the '
                        './pipelines directory.')
    parser.add_argument('--context', dest='pipeline_context',
                        help='String for context values. Parsed by the '
                        'pipeline\'s context_parser function.')
    parser.add_argument('--dir', dest='working_dir', default=os.getcwd(),
                        help='Working directory. Use if your pipelines '
                        'directory is elsewhere. Defaults to cwd.')
    parser.add_argument('--loglevel', dest='log_level', type=int, default=20,
                        help='Integer log level. Defaults to 20 (INFO). '
                        '10=DEBUG\n20=INFO\n30=WARNING\n40=ERROR\n50=CRITICAL'
                        '.\n Log Level < 10 gives full traceback on errors.')
    parser.add_argument('--version', action='version',
                        help='Echo version number.',
                        version=f'{pypyr.version.get_version()}')
    return parser


def main(args=None):
    """Entry point for pypyr cli.

    The setup_py entry_point wraps this in sys.exit already so this effectively
    becomes sys.exit(main()).
    The __main__ entry point similarly wraps sys.exit().
    """
    if args is None:
        args = sys.argv[1:]

    parsed_args = get_args(args)

    try:
        return pypyr.pipelinerunner.main(
            pipeline_name=parsed_args.pipeline_name,
            pipeline_context_input=parsed_args.pipeline_context,
            working_dir=parsed_args.working_dir,
            log_level=parsed_args.log_level)
    except KeyboardInterrupt:
        # Shell standard is 128 + signum = 130 (SIGINT = 2)
        sys.stdout.write("\n")
        return 128 + signal.SIGINT
    except Exception as e:
        # stderr and exit code 255
        sys.stderr.write("\n")
        sys.stderr.write(f"\033[91m{type(e).__name__}: {str(e)}\033[0;0m")
        sys.stderr.write("\n")
        # at this point, you're guaranteed to have args and thus log_level
        if parsed_args.log_level < 10:
            # traceback prints to stderr by default
            traceback.print_exc()

        return 255
