"""pypyr pipeline runner.

This is the entrypoint for the pypyr API.

Use run() to run a pipeline.
"""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
import copy
import logging
from os import PathLike
from pathlib import Path

from pypyr.config import config
from pypyr.context import Context
import pypyr.errors
from pypyr.pipeline import Pipeline

logger = logging.getLogger(__name__)


def run(
    pipeline_name: str,
    args_in: list[str] | None = None,
    parse_args: bool | None = None,
    dict_in: dict | None = None,
    groups: list[str] | None = None,
    success_group: str | None = None,
    failure_group: str | None = None,
    loader: str | None = None,
    py_dir: str | bytes | PathLike | None = None
) -> Context:
    """Run a pipeline. pypyr's entrypoint.

    Call me if you want to run a pypyr pipeline from your own code.

    If you want to run a pipeline exactly like the cli does, use args_in to
    pass a list of str arguments for the pipeline's context_parser. If you
    already have a dict-like structure you want to use to initialize context,
    use dict_in instead. If you provide dict_in and no args_in, pypyr will
    assume you mean not to run the context_parser on the pipeline
    (parse_args=False) - if you do want to run the context_parser in this case,
    explicitly set parse_args=True.

    If you're invoking pypyr from your own application via the API, it's your
    responsibility to set up and configure logging. If you just want to
    replicate the log handlers & formatters that the pypyr cli uses, you can
    call pypyr.log.logger.set_root_logger() once and only once before invoking
    run() for every pipeline you want to run.

    Be aware that pypyr adds a NOTIFY - 25 custom log-level and notify()
    function to logging.

    {pipeline_name}.yaml should resolve from the current working directory if
    you are using the default file loader.

    You only need to specify py_dir if your pipeline relies on custom modules
    that are NOT installed in the current Python environment. For convenience,
    pypyr allows pipeline authors to use ad hoc python modules that are not
    installed in the current environment by looking for these in py_dir 1st.

    Regardless of whether you set py_dir or not, be aware that if you are using
    the default file loader, pypyr will also add the pipeline's immediate
    parent directory to sys.path (only if it's not been added already), so that
    each pipeline can reference ad hoc modules relative to itself in the
    filesystem.

    Therefore you do NOT need to set py_dir if your ad hoc custom modules are
    relative to the pipeline itself.

    If your pipelines are only using built-in functionality, you don't need to
    set py_dir.

    If pipeline_name found in config.shortcuts, will use the configured values
    from the shortcut to find & run the pipeline. If a shortcut does not have
    a value for a particular argument, will fallback to the run() function's
    inputs, if any. If you pass args_in and/or dict_in and a shortcut is found
    for pipeline_name, will merge the function's input arguments into the
    shortcut's pipe_arg and args respectively.

    Example: Run ./dir/pipe-name.yaml, resolve ad hoc custom modules from the
    current directory and initialize context with dict {'a': 'b'}:

    context = run('dir/pipe-name', dict_in={'a': 'b'}, py_dir=Path.cwd())

    Args:
        pipeline_name (str): Name of pipeline, sans .yaml at end.
        args_in (list[str]): All the input arguments after the pipeline name
            from cli.
        parse_args (bool): run context_parser in pipeline. Default True.
        dict_in (dict): Dict-like object to initialize the Context.
        groups: (list[str]): Step-group names to run in pipeline.
            Default is ['steps'].
        success_group (str): Step-group name to run on success completion.
            Default is on_success.
        failure_group: (str): Step-group name to run on pipeline failure.
            Default is on_failure.
        loader (str): optional. Absolute name of pipeline loader module.
            If not specified will use pypyr.loaders.file.
        py_dir (Path-like): Custom python modules resolve from this dir.

    Returns:
        pypyr.context.Context(): The pypyr context as it is after the pipeline
                                  completes.
    """
    logger.debug("starting pypyr")

    if config.shortcuts:
        # assuming shortcuts is mostly empty dict, much faster to do truthy if
        # check before .get(), even though it looks redundant.
        shortcut = config.shortcuts.get(pipeline_name)
        if shortcut:
            shortcut_name = pipeline_name
            logger.debug("found shortcut in config for %s", shortcut_name)
            pipeline_name = shortcut.get('pipeline_name')
            if not pipeline_name:
                raise pypyr.errors.ConfigError(
                    f"shortcut '{shortcut_name}' has no pipeline_name set. "
                    "You must set pipeline_name for this shortcut in config "
                    "so that pypyr knows which pipeline to run.")
            pipe_arg = shortcut.get('pipe_arg')
            if pipe_arg:
                if isinstance(pipe_arg, str):
                    raise pypyr.errors.ConfigError(
                        f"shortcut '{shortcut_name}' pipe_arg should be a "
                        "list, not a string.")
                # append args_in to shortcut's pipe_args
                args_in = pipe_arg + args_in if args_in else pipe_arg

            skip_parse = shortcut.get('skip_parse')
            # flip the bit - skip_args means inverse of parse_args, but only
            # if it exists
            parse_args = skip_parse if skip_parse is None else not skip_parse

            shortcut_dict_in = shortcut.get('args')
            if shortcut_dict_in:
                # deepcopy so downstream mutations don't touch the original
                # dict in config
                sc_dict = copy.deepcopy(shortcut_dict_in)
                if dict_in:
                    # merge dict_in into shortcut's args
                    sc_dict.update(dict_in)
                dict_in = sc_dict

            sc_groups = shortcut.get('groups', groups)
            # if config specified a str, take it to mean a single group
            groups = [sc_groups] if isinstance(sc_groups, str) else sc_groups

            success_group = shortcut.get('success', success_group)
            failure_group = shortcut.get('failure', failure_group)
            loader = shortcut.get('loader', loader)
            dir_str = shortcut.get('py_dir')
            if dir_str:
                # will still honor cwd for cli if not set, since it'll only
                # override input if shortcut dir actually set.
                py_dir = Path(dir_str)

    parse_input = _get_parse_input(parse_args=parse_args,
                                   args_in=args_in,
                                   dict_in=dict_in)

    context = Context(dict_in) if dict_in else Context()

    pipeline = Pipeline(name=pipeline_name,
                        context_args=args_in,
                        parse_input=parse_input,
                        loader=loader,
                        groups=groups,
                        success_group=success_group,
                        failure_group=failure_group,
                        py_dir=py_dir)

    pipeline.run(context)

    logger.debug("pypyr done")

    return context


def _get_parse_input(parse_args, args_in, dict_in):
    """Return default for parse_input.

    This is to decide if context_parser should run or not.

    To make it easy on an API consumer, default behavior is ALWAYS to run
    parser UNLESS dict_in initializes context and there is no args_in.

    If dict_in specified, but no args_in: False
    If dict_in specified, AND args_in too: True
    If no dict_in specified, but args_in is: True
    If no dict_in AND no args_in: True
    If parse_args explicitly set, always honor its value.

    Args:
        parse_args (bool): Whether to run context parser.
        args_in (list[str]): String arguments as passed from the cli.
        dict_in (dict): Initialize context with this dict.

    Returns:
        Boolean. True if should parse input.
    """
    if parse_args is None:
        return not (args_in is None and dict_in is not None)

    return parse_args
