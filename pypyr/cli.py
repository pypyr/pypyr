"""cli entry point for pipeline runner.

Parse command line arguments in, invoke pipelinerunner.
"""
import argparse
from pathlib import Path
import pypyr.log.logger
import pypyr.pipelinerunner
import pypyr.version
import signal
import sys
import textwrap
import traceback


def wrap(text, **kwargs):
    """Wrap lines in argparse so they align nicely in 2 columns.

    Default width is 70.

    With gratitude to paul.j3 https://bugs.python.org/issue12806"""
    # apply textwrap to each line individually
    text = text.splitlines()
    text = [textwrap.fill(line, **kwargs) for line in text]
    return '\n'.join(text)


def get_args(args):
    """Parse arguments passed in from shell."""
    return get_parser().parse_args(args)


def get_parser():
    """Return ArgumentParser for pypyr cli."""
    parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='pypyr pipeline runner',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('pipeline_name',
                        help=wrap('Name of pipeline to run. It should exist '
                                  'in the ./pipelines directory.'))
    parser.add_argument(dest='context_args',
                        nargs='*',
                        default=None,
                        help=wrap('Initialize context with this. Parsed by '
                                  'the pipeline\'s context_parser function.\n'
                                  'Separate multiple args with spaces.'))
    parser.add_argument('--groups', dest='groups',
                        nargs='*',
                        default=None,
                        help=wrap(
                            'Step-Groups to run. defaults to "steps".\n'
                            'You probably want to order --groups AFTER the '
                            'pipeline name and context positional args. e.g\n'
                            'pypyr pipename context --groups group1 group2\n'
                            'If you prefer putting them before, use a -- to '
                            'separate groups from the pipeline name, e.g\n'
                            'pypyr --groups group1 group2 -- pipename context')
                        )
    parser.add_argument('--success', dest='success_group', default=None,
                        help=wrap(
                            'Step-Group to run on successful completion of '
                            'pipeline.\n'
                            'Defaults to "on_success"'))
    parser.add_argument('--failure', dest='failure_group', default=None,
                        help=wrap(
                            'Step-Group to run on error completion of '
                            'pipeline.\n'
                            'Defaults to "on_failure"'))
    parser.add_argument('--dir', dest='working_dir', default=Path.cwd(),
                        help=wrap('Working directory. Use if your pipelines '
                                  'directory is elsewhere.\n'
                                  'Defaults to cwd.'))
    parser.add_argument('--log', '--loglevel', dest='log_level', type=int,
                        default=25,
                        help=wrap(
                            'Integer log level. Defaults to 25 (NOTIFY).\n'
                            '10=DEBUG \n'
                            '20=INFO\n'
                            '25=NOTIFY\n'
                            '30=WARNING\n'
                            '40=ERROR\n'
                            '50=CRITICAL\n'
                            'Log Level < 10 gives full traceback on errors.'))
    parser.add_argument('--logpath', dest='log_path',
                        help=wrap(
                            'Log-file path. Append log output to this path.'))
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
        pypyr.log.logger.set_root_logger(log_level=parsed_args.log_level,
                                         log_path=parsed_args.log_path)

        return pypyr.pipelinerunner.main(
            pipeline_name=parsed_args.pipeline_name,
            pipeline_context_input=parsed_args.context_args,
            working_dir=parsed_args.working_dir,
            groups=parsed_args.groups,
            success_group=parsed_args.success_group,
            failure_group=parsed_args.failure_group)
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
