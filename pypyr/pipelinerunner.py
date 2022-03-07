"""pypyr pipeline runner.

This is the entrypoint for the pypyr API.

Use run() to run a pipeline.
"""
# can remove __future__ once py 3.10 the lowest supported version
from __future__ import annotations
import logging
from os import PathLike

from pypyr.context import Context
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

    pipeline, args = Pipeline.new_pipe_and_args(name=pipeline_name,
                                                context_args=args_in,
                                                parse_input=parse_args,
                                                dict_in=dict_in,
                                                loader=loader,
                                                groups=groups,
                                                success_group=success_group,
                                                failure_group=failure_group,
                                                py_dir=py_dir)

    context = Context(args) if args else Context()

    pipeline.run(context)

    logger.debug("pypyr done")

    return context
